'''The Hivemind'''

import queue
import time
import numpy as np

from rlbot.botmanager.agent_metadata import AgentMetadata
from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils import rate_limiter
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.game_state_util import Vector3, Rotator

PI = np.pi

class ExampleHivemind(BotHelperProcess):

    # Some terminology:
    # hivemind = the process which controls the drones.
    # drone = a bot under the hivemind's control.

    def __init__(self, agent_metadata_queue, quit_event, options):
        super().__init__(agent_metadata_queue, quit_event, options)

        # Sets up the logger. The string is the name of your hivemind.
        # Call this something unique so people can differentiate between hiveminds.
        self.logger = get_logger('Example Hivemind')

        # The game interface is how you get access to things
        # like ball prediction, the game tick packet, or rendering.
        self.game_interface = GameInterface(self.logger)

        # Running indices is a set of bot indices
        # which requested this hivemind with the same key.
        self.running_indices = set()


    def try_receive_agent_metadata(self):
        while True:  # will exit on queue.Empty
            try:
                # Adds drone indices to running_indices.
                single_agent_metadata: AgentMetadata = self.metadata_queue.get(timeout=0.1)
                self.running_indices.add(single_agent_metadata.index)
            except queue.Empty:
                return
            except Exception as ex:
                self.logger.error(ex)


    def start(self):
        """Runs once, sets up the hivemind and its agents."""
        # Prints an activation message into the console.
        # This let's you know that the process is up and running.
        self.logger.info("Hello World!")
        
        # Loads game interface.
        self.game_interface.load_interface()

        # Wait a moment for all agents to have a chance to start up and send metadata.
        self.logger.info("Sleeping for 3 seconds; give it a moment.")
        time.sleep(3)
        self.try_receive_agent_metadata()
        
        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()

            
    def game_loop(self):
        """The main game loop. This is where your hivemind code goes."""

        # Setting up rate limiter.
        rate_limit = rate_limiter.RateLimiter(120)

        # This is how you access field info.
        # First create the initialise the object...
        field_info = FieldInfoPacket()
        # Then update it.
        self.game_interface.update_field_info_packet(field_info)

        # Same goes for the packet, but that is
        # also updated in the main loop every tick.
        packet = GameTickPacket()
        self.game_interface.update_live_data_packet(packet)

        # Same pattern follows with ball predition.
        self.ball_prediction = BallPrediction()
        self.game_interface.update_ball_prediction(self.ball_prediction)

        # Create a Ball object for the ball that holds its information.        
        self.ball = Ball()

        # Create a Drone object for every drone that holds its information.
        self.drones = []
        for index in range(packet.num_cars):
            if index in self.running_indices:
                self.drones.append(Drone(index, packet.game_cars[index].team))

        self.game_time = 0.0
        self.pinch_target = None
        self.pinch_time = 0.0

        # MAIN LOOP:
        while True:

            # PRE-PROCESSING:
            # Updating the game packet from the game.
            self.game_interface.update_live_data_packet(packet)

            # Updates the ball prediction.          
            self.game_interface.update_ball_prediction(self.ball_prediction)

            # Processing ball data.
            self.ball.pos = a3v(packet.game_ball.physics.location)
            self.ball.vel = a3v(packet.game_ball.physics.velocity)

            # Processing drone data.
            for drone in self.drones:
                drone.pos = a3v(packet.game_cars[drone.index].physics.location)
                drone.rot = a3r(packet.game_cars[drone.index].physics.rotation)
                drone.vel = a3v(packet.game_cars[drone.index].physics.velocity)
                drone.orient_m = orient_matrix(drone.rot)

                # Reset ctrl every tick.
                drone.ctrl = PlayerInput()

            # Game time.
            self.game_time = packet.game_info.seconds_elapsed


            # TEAM PINCH CODE:
            # Sorts drones based on distance to ball.
            sorted_drones = sorted(self.drones, key=lambda drone: np.linalg.norm(drone.pos - self.ball.pos))

            if self.game_time > self.pinch_time:
                self.pinch_target = None

            if self.pinch_target is None:
                # Gets a rough estimate for which target locations are possible.
                second_closest_drone = sorted_drones[1]
                rough_estimate = np.linalg.norm(self.ball.pos - second_closest_drone.pos) / 1400 + 2

                # Filters out all that are sooner than our rough estimate.
                valid_targets = [step for step in self.ball_prediction.slices if step.game_seconds > self.game_time + rough_estimate]
                # Filters out all that are higher in the air.
                valid_targets = [step for step in valid_targets if step.physics.location.z < 100]
                
                if len(valid_targets) > 0:
                    self.pinch_target = a3v(valid_targets[0].physics.location)
                    self.pinch_time = valid_targets[0].game_seconds

            # Checks if the ball has been hit recently
            elif packet.game_ball.latest_touch.time_seconds + 0.2 > self.game_time:
                self.pinch_target = None

            else:
                # Get closest bots to attempt a team pinch.
                pinch_drones = sorted_drones[:2]
                self.team_pinch(pinch_drones)

            # Use this to send the drone inputs to the drones.
            for drone in self.drones:
                self.game_interface.update_player_input(drone.ctrl, drone.index)

            # Some debug rendering.
            self.draw_debug()



            # Rate limit sleep.
            rate_limit.acquire()


    def draw_debug(self):
        """Renders the ball prediction and drone indices."""
        self.game_interface.renderer.begin_rendering('debug')

        # Renders ball prediction
        path = [step.physics.location for step in self.ball_prediction.slices]
        self.game_interface.renderer.draw_polyline_3d(path, self.game_interface.renderer.pink())

        # Renders drone indices.
        for drone in self.drones:
            self.game_interface.renderer.draw_string_3d(drone.pos, 1, 1, str(drone.index), self.game_interface.renderer.white())

        # Team pinch info.
        if self.pinch_target is not None:
            self.game_interface.renderer.draw_rect_3d(self.pinch_target, 10, 10, True, self.game_interface.renderer.red())
            self.game_interface.renderer.draw_string_2d(10,10,2,2,str(self.pinch_time-self.game_time),self.game_interface.renderer.red())

        self.game_interface.renderer.end_rendering()


    def team_pinch(self, pinch_drones):
        # Finds time remaining to pinch.
        time_remaining = self.pinch_time - self.game_time

        for i, drone in enumerate(pinch_drones):
            # Finds vector towards goal from pinch target location.
            vector_to_goal = normalise(goal_pos*team_sign(drone.team)-self.pinch_target)
            # Finds 2D vector towards goal from pinch target.
            angle_to_goal = np.arctan2(vector_to_goal[1],vector_to_goal[0])
            # Angle offset for each bot participating in pinch.
            angle_offset = 2*PI / (len(pinch_drones) + 1)
            # Calculating approach vector.
            approach_angle = angle_to_goal + angle_offset * (i+1)
            approach_vector = np.array([np.cos(approach_angle), np.sin(approach_angle), 0])

            # Calculate target velocity
            distance_to_target = np.linalg.norm(self.pinch_target - drone.pos)
            target_velocity = distance_to_target / time_remaining
            # Offset target from the pinch target to drive towards.
            drive_target = self.pinch_target + (approach_vector * distance_to_target/2)
            # Calculates the pinch location in local coordinates.
            local_target = local(drone.orient_m, drone.pos, drive_target)
            # Finds 2D angle to target. Positive is clockwise.
            angle = np.arctan2(local_target[1], local_target[0])

            # Smooths out steering with modified sigmoid funcion.
            def special_sauce(x, a):
                """Modified sigmoid."""
                # Graph: https://www.geogebra.org/m/udfp2zcy
                return 2 / (1 + np.exp(a*x)) - 1

            # Calculates steer.
            drone.ctrl.steer = special_sauce(angle, -5)

            # Throttle controller.
            local_velocity = local(drone.orient_m, a3l([0,0,0]), drone.vel)
            # If I'm facing the wrong way, do a little drift.
            if abs(angle) > 1.6:
                drone.ctrl.throttle = 1.0
                drone.ctrl.handbrake = True
            else:
                drone.ctrl.throttle = 1 if local_velocity[0] < target_velocity else 0.0

            '''
            # Dodge at the very end to pinch the ball.
            if 0.15 < time_remaining < 0.2:
                drone.ctrl.jump = True

            elif 0.0 < self.pinch_time - self.game_time  < 0.1:
                drone.ctrl.pitch = -1
                drone.ctrl.jump = True
            '''

            # Rendering of approach vectors.
            self.game_interface.renderer.begin_rendering(f'approach vectors {i}')
            self.game_interface.renderer.draw_line_3d(self.pinch_target, drive_target, self.game_interface.renderer.green())
            self.game_interface.renderer.end_rendering()
                

# -----------------------------------------------------------

# UTILS:
# I copied over some of my HiveBot utils.
# Feel free to check out the full version if you'd like to use them.

class Drone:
    """Houses the processed data from the packet for the drones.

    Attributes:
        index {int} -- The car's index in the packet.
        team {int} -- 0 if blue, else 1.
        pos {np.ndarray} -- Position vector.
        rot {np.ndarray} -- Rotation (pitch, yaw, roll).
        vel {np.ndarray} -- Velocity vector.
        orient_m {np.ndarray} -- Orientation matrix.
        ctrl {PlayerInput} -- The controls we want to send to the drone.
    """
    __slots__ = [
        'index',
        'team',
        'pos',
        'rot',
        'vel',
        'orient_m',
        'ctrl'  
    ]

    def __init__(self, index : int, team : int):
        self.index      : int           = index
        self.team       : int           = team
        self.pos        : np.ndarray    = np.zeros(3)
        self.rot        : np.ndarray    = np.zeros(3)
        self.vel        : np.ndarray    = np.zeros(3)
        self.orient_m   : np.ndarray    = np.identity(3)
        self.ctrl       : PlayerInput   = PlayerInput()


class Ball:
    """Houses the processed data from the packet for the ball.

    Attributes:
        pos {np.ndarray} -- Position vector.
        vel {np.ndarray} -- Velocity vector.
    """
    __slots__ = [
        'pos',
        'vel'
    ]

    def __init__(self):
        self.pos        : np.ndarray    = np.zeros(3)
        self.vel        : np.ndarray    = np.zeros(3)

# -----------------------------------------------------------

# FUNCTIONS FOR CONVERTION TO NUMPY ARRAYS:

def a3l(L : list) -> np.ndarray:
    """Converts list to numpy array.

    Arguments:
        L {list} -- The list to convert containing 3 elemets.

    Returns:
        np.array -- Numpy array with the same contents as the list.
    """
    return np.array([L[0], L[1], L[2]])

def a3r(R : Rotator) -> np.ndarray:
    """Converts rotator to numpy array.

    Arguments:
        R {Rotator} -- Rotator class containing pitch, yaw, and roll.

    Returns:
        np.ndarray -- Numpy array with the same contents as the rotator.
    """
    return np.array([R.pitch, R.yaw, R.roll])


def a3v(V : Vector3) -> np.ndarray:
    """Converts vector3 to numpy array.

    Arguments:
        V {Vector3} -- Vector3 class containing x, y, and z.

    Returns:
        np.ndarray -- Numpy array with the same contents as the vector3.
    """
    return np.array([V.x, V.y, V.z])

# -----------------------------------------------------------

# LINEAR ALGEBRA:

def normalise(V : np.ndarray) -> np.ndarray:
    """Normalises a vector.
    
    Arguments:
        V {np.ndarray} -- Vector.
    
    Returns:
        np.ndarray -- Normalised vector.
    """
    magnitude = np.linalg.norm(V)
    if magnitude != 0.0:
        return V / magnitude
    else:
        return V

def orient_matrix(R : np.ndarray) -> np.ndarray:
    """Converts from Euler angles to an orientation matrix.

    Arguments:
        R {np.ndarray} -- Pitch, yaw, and roll.

    Returns:
        np.ndarray -- Orientation matrix of shape (3, 3).
    """
    # Credits to chip https://samuelpmish.github.io/notes/RocketLeague/aerial_control/
    pitch : float = R[0]
    yaw   : float = R[1]
    roll  : float = R[2]

    CR : float = np.cos(roll)
    SR : float = np.sin(roll)
    CP : float = np.cos(pitch)
    SP : float = np.sin(pitch)
    CY : float = np.cos(yaw)
    SY : float = np.sin(yaw)

    A = np.zeros((3, 3))

    # front direction
    A[0,0] = CP * CY
    A[1,0] = CP * SY
    A[2,0] = SP

    # right direction (should be left but for some reason it is weird)
    A[0,1] = CY * SP * SR - CR * SY
    A[1,1] = SY * SP * SR + CR * CY
    A[2,1] = -CP * SR

    # up direction
    A[0,2] = -CR * CY * SP - SR * SY
    A[1,2] = -CR * SY * SP + SR * CY
    A[2,2] = CP * CR

    return A


def local(A : np.ndarray, p0 : np.ndarray, p1 : np.ndarray) -> np.ndarray:
    """Transforms world coordinates into local coordinates.
    
    Arguments:
        A {np.ndarray} -- The local orientation matrix.
        p0 {np.ndarray} -- World x, y, and z coordinates of the start point for the vector.
        p1 {np.ndarray} -- World x, y, and z coordinates of the end point for the vector.
    
    Returns:
        np.ndarray -- Local x, y, and z coordinates.
    """
    return np.dot(A.T, p1 - p0)


def team_sign(team : int) -> int:
    """Gives the sign for a calculation based on team.
    
    Arguments:
        team {int} -- 0 if Blue, 1 if Orange.
    
    Returns:
        int -- 1 if Blue, -1 if Orange
    """
    return 1 if team == 0 else -1

goal_pos = a3l([0,5300,0])
    