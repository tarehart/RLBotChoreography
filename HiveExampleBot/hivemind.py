'''The Hivemind'''
import glob
import inspect
import os
import sys
import traceback

from rlbot.utils.class_importer import load_external_class, load_external_module
from rlbot.utils.structures.bot_input_struct import PlayerInput

from choreography.choreography import Choreography
from choreography.lightfall_choreography import LightfallChoreography

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import queue
import time
import numpy as np
from rlbot.agents.base_agent import SimpleControllerState

from rlbot.botmanager.agent_metadata import AgentMetadata
from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.game_state_util import Vector3, Rotator

from choreography.drone import Drone
from choreography.group_step import BlindBehaviorStep

PI = np.pi

# -----------------------------------------------------------

# PARAMETERS:

# Distance parameters for the range in which it will consider pinching.
CLOSEST = 1500.0
FARTHEST = 3500.0

# Extra time buffer.
# Gives time for drones to better align in PINCH state since they'll have more time.
TIME_BUFFER = 0.5

# Pessimistic time error.
# Makes drones start this bit earlier than they think they need to.
TIME_ERROR = -0.1

# Turn to pos wiggle rate per second.
RATE = 0.2

# Additional tweakable positions starting on line 187 for where bots will wait.
# More tweakable values directly in the controllers at the bottom.

# -----------------------------------------------------------

# THE HIVEMIND:

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

        self.lightfall_choreography = LightfallChoreography(self.game_interface)
        self.lightfall_choreography.generate_sequence()

        # self.hot_reloader = HotReloader(
        #     os.path.join(os.path.dirname(__file__), 'choreography/lightfall_choreography.py'), Choreography)

    def try_receive_agent_metadata(self):
        """Adds all drones with the correct key to our set of running indices."""
        while True:  # will exit on queue.Empty
            try:
                # Adds drone indices to running_indices.
                single_agent_metadata: AgentMetadata = self.metadata_queue.get(
                    timeout=0.1)
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

        # This is how you access field info.
        # First create the initialise the object...
        field_info = FieldInfoPacket()
        # Then update it.
        self.game_interface.update_field_info_packet(field_info)

        # Same goes for the packet, but that is
        # also updated in the main loop every tick.
        packet = GameTickPacket()
        self.game_interface.update_live_data_packet(packet)
        # Ball prediction works the same. Check the main loop.

        # Create a Ball object for the ball that holds its information.
        self.ball = Ball()

        # Create a Drone object for every drone that holds its information.
        self.drones = []

        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()



    def game_loop(self):
        """The main game loop. This is where your hivemind code goes."""

        # Creating packet and ball prediction objects which will be updated every tick.
        packet = GameTickPacket()
        ball_prediction = BallPrediction()

        # Nicknames the renderer to shorten code.
        draw = self.game_interface.renderer

        # MAIN LOOP:
        while True:

            prev_time = packet.game_info.seconds_elapsed
            # Updating the game tick packet.
            self.game_interface.update_live_data_packet(packet)

            # Checking if packet is new, otherwise sleep.
            if prev_time == packet.game_info.seconds_elapsed:
                time.sleep(0.001)

            else:
                # Begins rendering at the start of the loop; makes life easier.
                # https://discordapp.com/channels/348658686962696195/446761380654219264/610879527089864737
                draw.begin_rendering(f'Hivemind')

                # PRE-PROCESSING:

                # Updates the ball prediction.
                # self.game_interface.update_ball_prediction(ball_prediction)

                # Processing ball data.
                self.ball.pos = a3v(packet.game_ball.physics.location)

                # Create a Drone object for every drone that holds its information.
                if packet.num_cars > len(self.drones):
                    self.drones.clear()
                    for index in range(packet.num_cars):
                        self.drones.append(Drone(index, packet.game_cars[index].team))

                # Processing drone data.
                for drone in self.drones:
                    drone.pos = a3v(packet.game_cars[drone.index].physics.location)
                    drone.rot = a3r(packet.game_cars[drone.index].physics.rotation)
                    drone.vel = a3v(packet.game_cars[drone.index].physics.velocity)
                    drone.boost = packet.game_cars[drone.index].boost
                    drone.orient_m = orient_matrix(drone.rot)

                    # Reset ctrl every tick.
                    drone.ctrl = SimpleControllerState()

                self.lightfall_choreography.step(packet, self.drones)
                if self.lightfall_choreography.finished:
                    self.lightfall_choreography = LightfallChoreography(self.game_interface)
                    self.lightfall_choreography.generate_sequence()

                # Use this to send the drone inputs to the drones.
                for drone in self.drones:
                    self.game_interface.update_player_input(
                        convert_player_input(drone.ctrl), drone.index)

                # Some example rendering:

                # Renders drone indices.
                # for drone in self.drones:
                #     draw.draw_string_3d(drone.pos, 1, 1, str(
                #         drone.index), draw.white())

                # Ending rendering.
                draw.end_rendering()

# -----------------------------------------------------------


def convert_player_input(ctrl: SimpleControllerState) -> PlayerInput:
    player_input = PlayerInput()
    player_input.throttle = ctrl.throttle
    player_input.steer = ctrl.steer
    player_input.pitch = ctrl.pitch
    player_input.yaw = ctrl.yaw
    player_input.roll = ctrl.roll
    player_input.jump = ctrl.jump
    player_input.boost = ctrl.boost
    player_input.handbrake = ctrl.handbrake
    player_input.use_item = ctrl.use_item
    return player_input


class HotReloader:

    def __init__(self, reload_file, reload_base_class):
        self.last_module_modification_time = 0
        self.scan_last = 0
        self.scan_temp = 0
        self.file_iterator = None
        self.reload_file = reload_file
        self.reload_base_class = reload_base_class
        self.logger = get_logger('Hot Reloader')
        self.loaded_class = None

    def hot_reload_if_necessary(self):
        try:
            new_module_modification_time = self.check_modification_time(os.path.dirname(__file__))
            if new_module_modification_time != self.last_module_modification_time:
                self.last_module_modification_time = new_module_modification_time
                self.logger.info(f"Reloading {self.reload_file}")
                self.loaded_class, module = load_external_class(self.reload_file, self.reload_base_class)
        except FileNotFoundError:
            self.logger.error(f"Agent file was not found. Will try again.")
            time.sleep(0.5)
        except Exception:
            self.logger.error("Reloading the agent failed:\n" + traceback.format_exc())
            time.sleep(5)  # Avoid burning CPU, and give the user a moment to read the log

    def check_modification_time(self, directory, timeout_ms=1):
        if self.scan_last > 0 and timeout_ms is not None:
            stop_time = time.perf_counter_ns() + timeout_ms * 10**6
        else:
            stop_time = None
        if self.file_iterator is None:
            self.file_iterator = glob.iglob(f"{directory}/**/*.py", recursive=True)
        for f in self.file_iterator:
            self.scan_temp = max(self.scan_temp, os.stat(f).st_mtime)
            if stop_time is not None and time.perf_counter_ns() > stop_time:
                # Timeout exceeded. The scan will pick up from here on the next call.
                break
        else:
            # Scan finished. Update the modification time and restart the scan:
            self.scan_last, self.scan_temp = self.scan_temp, 0
            self.file_iterator = None
        return self.scan_last



# CONTROLLERS:

def slow_to_pos(drone, position):
    # Calculate distance and velocity.
    distance = np.linalg.norm(position - drone.pos)
    velocity = np.linalg.norm(drone.vel)
    # Calculates the target position in local coordinates.
    local_target = local(drone.orient_m, drone.pos, position)
    # Finds 2D angle to target. Positive is clockwise.
    angle = np.arctan2(local_target[1], local_target[0])

    def special_sauce(x, a):
        """Modified sigmoid to smooth out steering."""
        # Graph: https://www.geogebra.org/m/udfp2zcy
        return 2 / (1 + np.exp(a*x)) - 1

    # Calculates steer.
    drone.ctrl.steer = special_sauce(angle, -5)

    # Throttle controller.
    if abs(angle) > 2:
        # If I'm facing the wrong way, do a little drift.
        drone.ctrl.throttle = 1.0
        drone.ctrl.handbrake = True
    elif distance > 100:
        # A simple PD controller to stop at target.
        drone.ctrl.throttle = cap(0.3*distance - 0.2*velocity, -1.0, 1.0)


def turn_to_pos(drone, position, game_time):
    # Calculates the target position in local coordinates.
    local_target = local(drone.orient_m, drone.pos, position)
    # Finds 2D angle to target. Positive is clockwise.
    angle = np.arctan2(local_target[1], local_target[0])

    # Toggles forward.
    drone.forward = round(game_time / RATE) % 2

    # Wiggles forward and back switching the steer to rotate on the spot.
    if drone.forward:
        drone.ctrl.throttle = 0.5
        drone.ctrl.steer = cap(angle, -1, 1)
    else:
        drone.ctrl.throttle = -0.5
        drone.ctrl.steer = cap(-angle, -1, 1)


def fast_to_pos(drone, position):
    # Calculates the target position in local coordinates.
    local_target = local(drone.orient_m, drone.pos, position)
    # Finds 2D angle to target. Positive is clockwise.
    angle = np.arctan2(local_target[1], local_target[0])

    def special_sauce(x, a):
        """Modified sigmoid to smooth out steering."""
        # Graph: https://www.geogebra.org/m/udfp2zcy
        return 2 / (1 + np.exp(a*x)) - 1

    # Control towards hit position. Fully boosting.
    drone.ctrl.steer = special_sauce(angle, -5)
    drone.ctrl.throttle = 1.0
    drone.ctrl.boost = True

# -----------------------------------------------------------

# UTILS:
# I copied over some of my HiveBot utils.
# Feel free to check out the full utilities file of HiveBot.



class Ball:
    """Houses the processed data from the packet for the ball.

    Attributes:
        pos {np.ndarray} -- Position vector.
    """
    __slots__ = [
        'pos'
    ]

    def __init__(self):
        self.pos: np.ndarray = np.zeros(3)


# -----------------------------------------------------------

# FUNCTIONS FOR CONVERTION TO NUMPY ARRAYS:

def a3l(L: list) -> np.ndarray:
    """Converts list to numpy array.

    Arguments:
        L {list} -- The list to convert containing 3 elemets.

    Returns:
        np.array -- Numpy array with the same contents as the list.
    """
    return np.array([L[0], L[1], L[2]])


def a3r(R: Rotator) -> np.ndarray:
    """Converts rotator to numpy array.

    Arguments:
        R {Rotator} -- Rotator class containing pitch, yaw, and roll.

    Returns:
        np.ndarray -- Numpy array with the same contents as the rotator.
    """
    return np.array([R.pitch, R.yaw, R.roll])


def a3v(V: Vector3) -> np.ndarray:
    """Converts vector3 to numpy array.

    Arguments:
        V {Vector3} -- Vector3 class containing x, y, and z.

    Returns:
        np.ndarray -- Numpy array with the same contents as the vector3.
    """
    return np.array([V.x, V.y, V.z])

# -----------------------------------------------------------

# LINEAR ALGEBRA:

def orient_matrix(R: np.ndarray) -> np.ndarray:
    """Converts from Euler angles to an orientation matrix.

    Arguments:
        R {np.ndarray} -- Pitch, yaw, and roll.

    Returns:
        np.ndarray -- Orientation matrix of shape (3, 3).
    """
    # Credits to chip https://samuelpmish.github.io/notes/RocketLeague/aerial_control/
    pitch: float = R[0]
    yaw: float = R[1]
    roll: float = R[2]

    CR: float = np.cos(roll)
    SR: float = np.sin(roll)
    CP: float = np.cos(pitch)
    SP: float = np.sin(pitch)
    CY: float = np.cos(yaw)
    SY: float = np.sin(yaw)

    A = np.zeros((3, 3))

    # front direction
    A[0, 0] = CP * CY
    A[1, 0] = CP * SY
    A[2, 0] = SP

    # right direction (should be left but for some reason it is weird)
    A[0, 1] = CY * SP * SR - CR * SY
    A[1, 1] = SY * SP * SR + CR * CY
    A[2, 1] = -CP * SR

    # up direction
    A[0, 2] = -CR * CY * SP - SR * SY
    A[1, 2] = -CR * SY * SP + SR * CY
    A[2, 2] = CP * CR

    return A


def local(A: np.ndarray, p0: np.ndarray, p1: np.ndarray) -> np.ndarray:
    """Transforms world coordinates into local coordinates.

    Arguments:
        A {np.ndarray} -- The local orientation matrix.
        p0 {np.ndarray} -- World x, y, and z coordinates of the start point for the vector.
        p1 {np.ndarray} -- World x, y, and z coordinates of the end point for the vector.

    Returns:
        np.ndarray -- Local x, y, and z coordinates.
    """
    return np.dot(A.T, p1 - p0)

# -----------------------------------------------------------

# OTHER:

def team_sign(team: int) -> int:
    """Gives the sign for a calculation based on team.

    Arguments:
        team {int} -- 0 if Blue, 1 if Orange.

    Returns:
        int -- 1 if Blue, -1 if Orange
    """
    return 1 if team == 0 else -1


def cap(value: float, minimum: float, maximum: float) -> float:
    """Caps the value at given minumum and maximum.

    Arguments:
        value {float} -- The value being capped.
        minimum {float} -- Smallest value.
        maximum {float} -- Largest value.

    Returns:
        float -- The capped value or the original value if within range.
    """
    if value > maximum:
        return maximum
    elif value < minimum:
        return minimum
    else:
        return value


def make_circle(radius, centre, n):
    """Returns n number of points on a circle.

    Currently assumes that you want the circle on the XY plane, at height 20.

    Arguments:
        radius {float} -- Radius of the circle.
        centre {np.ndarray} -- Centre of the circle.
        n {int} -- Number of points to generate.
    """
    theta = np.linspace(0, 2*PI, n).reshape((n, 1))
    x = np.cos(theta)*radius
    y = np.sin(theta)*radius
    z = np.ones_like(x)*20
    circle = np.concatenate((x, y, z), axis=1)
    return circle + centre
