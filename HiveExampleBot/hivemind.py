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

        # Wait a moment for all agents to have a chance to start up and send metadata.
        self.logger.info("Snoozing for 3 seconds; give me a moment.")
        time.sleep(3)
        self.try_receive_agent_metadata()

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
        for index in range(packet.num_cars):
            if index in self.running_indices:
                self.drones.append(Drone(index, packet.game_cars[index].team))

        # Other attribute initialisation.
        self.state = State.SETUP
        self.pinch_target = None

        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()

    def game_loop(self):
        """The main game loop. This is where your hivemind code goes."""

        # Setting up rate limiter.
        rate_limit = rate_limiter.RateLimiter(120)

        # Creating packet and ball prediction objects which will be updated every tick.
        packet = GameTickPacket()
        ball_prediction = BallPrediction()

        # Nicknames the renderer to shorten code.
        draw = self.game_interface.renderer

        # MAIN LOOP:
        while True:

            # Begins rendering at the start of the loop; makes life easier.
            # https://discordapp.com/channels/348658686962696195/446761380654219264/610879527089864737
            draw.begin_rendering(f'Hivemind{self.drones[0].team}')

            # PRE-PROCESSING:
            # Updating the game packet from the game.
            self.game_interface.update_live_data_packet(packet)

            # Updates the ball prediction.
            self.game_interface.update_ball_prediction(ball_prediction)

            # Processing ball data.
            self.ball.pos = a3v(packet.game_ball.physics.location)

            # Processing drone data.
            for drone in self.drones:
                drone.pos = a3v(packet.game_cars[drone.index].physics.location)
                drone.rot = a3r(packet.game_cars[drone.index].physics.rotation)
                drone.vel = a3v(packet.game_cars[drone.index].physics.velocity)
                drone.boost = packet.game_cars[drone.index].boost
                drone.orient_m = orient_matrix(drone.rot)

                # Reset ctrl every tick.
                # PlayerInput is practically identical to SimpleControllerState.
                drone.ctrl = PlayerInput()

            # Game time.
            game_time = packet.game_info.seconds_elapsed

            # Example Team Pinches (2 bots only)
            # There's nothing stopping you from doing it with more ;) Give it a shot!
            if len(self.drones) == 2:

                # Sorts the drones left to right. (More understandble code below)
                #right_to_left_drones = sorted(self.drones, key=lambda drone: drone.pos[0]*team_sign(drone.team))

                # Finds the right and left drones.
                sign = team_sign(self.drones[0].team)
                if self.drones[0].pos[0]*sign <= self.drones[1].pos[0]*sign:
                    right = self.drones[0]
                    left = self.drones[1]
                else:
                    right = self.drones[1]
                    left = self.drones[0]

                # Bots get boost and go to wait positions.
                if self.state == State.SETUP:

                    # Some guide positions.
                    right_boost = a3l([-3072.0, -4096.0, 71.1])*sign
                    right_wait = a3l([-1792.0, -4184.0, 71.1])*sign
                    # Making use of symmetry
                    left_boost = right_boost * a3l([-1, 1, 1])
                    left_wait = right_wait * a3l([-1, 1, 1])

                    # First get boost and then go to wait position.
                    if right.boost < 100:
                        slow_to_pos(right, right_boost)
                    else:
                        slow_to_pos(right, right_wait)

                    if left.boost < 100:
                        slow_to_pos(left, left_boost)
                    else:
                        slow_to_pos(left, left_wait)

                    # If both bots are in wait position, switch to WAIT state.
                    if np.linalg.norm(right.pos-right_wait) + np.linalg.norm(left.pos-left_wait) < 200:
                        self.state = State.WAIT

                # Bots try to face the ball, waiting for perfect moment to team pinch.
                elif self.state == State.WAIT:

                    # Each drone should try to face the ball.
                    for drone in self.drones:
                        turn_to_pos(drone, self.ball.pos, game_time)

                    # Filters out all the predictions where the ball is too far off the ground.
                    # Result is a list of tuples of positions and time.
                    filtered_prediction = [(a3v(step.physics.location), step.game_seconds)
                                           for step in ball_prediction.slices if step.physics.location.z < 100]

                    if len(filtered_prediction) > 0:
                        # Turns the predition into a numpy array for fast vectorized calculations.
                        filtered_prediction = np.array(filtered_prediction)

                        # Gets the vectors from the drones to the ball prediction.
                        positions = np.vstack(filtered_prediction[:, 0])
                        right_to_prediction = positions - right.pos
                        left_to_prediction = positions - left.pos

                        # Calculates the distances.
                        # Cool blog post about einsum: http://ajcr.net/Basic-guide-to-einsum/
                        right_distances = np.sqrt(
                            np.einsum('ij,ij->i', right_to_prediction, right_to_prediction))
                        left_distances = np.sqrt(
                            np.einsum('ij,ij->i', left_to_prediction, left_to_prediction))

                        # Filters out the predictions which are too close or too far.
                        good_distances = (CLOSEST <= right_distances) & (FARTHEST >= right_distances) & (
                            CLOSEST <= left_distances) & (FARTHEST >= left_distances)
                        valid_targets = filtered_prediction[good_distances]

                        if len(valid_targets) > 0:
                            # Getting the remaining distances after filter.
                            right_distances = right_distances[good_distances]
                            left_distances = left_distances[good_distances]

                            # Getting time estimates to go that distance. (Assuming boosting, and going in a straight line.)
                            # https://www.geogebra.org/m/nnsat4pj
                            right_times = right_distances**0.55 / 41.53
                            right_times[right_distances > 2177.25] = 1/2300 * \
                                right_distances[right_distances > 2177.25] + 0.70337
                            right_times += game_time + TIME_BUFFER

                            left_times = left_distances**0.55 / 41.53
                            left_times[left_distances > 2177.25] = 1/2300 * \
                                left_distances[left_distances > 2177.25] + 0.70337
                            left_times += game_time + TIME_BUFFER

                            # Filters out the predictions which we can't get to.
                            good_times = (valid_targets[:, 1] > right_times) & (
                                valid_targets[:, 1] > left_times)
                            valid_targets = valid_targets[good_times]

                            # To avoid flukes or anomalies, check that the ball is valid for at least 10 steps.
                            # Not exact because there could be more bounce spots but good enough to avoid flukes.
                            if len(valid_targets) > 10:
                                # Select first valid target.
                                self.pinch_target = valid_targets[0]
                                # Reset drone's going attribute.
                                right.going = False
                                left.going = False
                                # Set the state to PINCH.
                                self.state = State.PINCH

                    # Rendering number of positions viable after each condition.
                    draw.draw_string_2d(
                        10, 70, 2, 2, f'Good height: {len(filtered_prediction)}', draw.white())
                    draw.draw_string_2d(
                        10, 100, 2, 2, f'Good distance: {len(valid_targets)}', draw.white())
                    # Render circles to show distances.
                    draw.draw_polyline_3d(make_circle(
                        CLOSEST, right.pos, 20), draw.cyan())
                    draw.draw_polyline_3d(make_circle(
                        CLOSEST, left.pos, 20), draw.cyan())
                    draw.draw_polyline_3d(make_circle(
                        FARTHEST, right.pos, 30), draw.pink())
                    draw.draw_polyline_3d(make_circle(
                        FARTHEST, left.pos, 30), draw.pink())

                elif self.state == State.PINCH:

                    # Checks if the ball has been hit recently.
                    if packet.game_ball.latest_touch.time_seconds + 0.1 > game_time:
                        self.pinch_target = None
                        self.state = State.SETUP

                    elif self.pinch_target is not None:
                        if not right.going:
                            # Get the distance to the target.
                            right_distance = np.linalg.norm(
                                self.pinch_target[0] - right.pos)
                            # Get a time estimate
                            right_time = right_distance**0.55 / \
                                41.53 if right_distance <= 2177.25 else 1/2300 * right_distance + 0.70337

                            # Waits until time is right to go. Otherwise turns to face the target position.
                            if game_time + right_time + TIME_ERROR >= self.pinch_target[1]:
                                right.going = True
                            else:
                                turn_to_pos(
                                    right, self.pinch_target[0], game_time)

                        else:
                            fast_to_pos(right, self.pinch_target[0])

                        # Same for left.
                        if not left.going:
                            left_distance = np.linalg.norm(
                                self.pinch_target[0] - left.pos)
                            left_time = left_distance**0.55 / \
                                41.53 if left_distance <= 2177.25 else 1/2300 * left_distance + 0.70337
                            if game_time + left_time + TIME_ERROR >= self.pinch_target[1]:
                                left.going = True
                            else:
                                turn_to_pos(
                                    left, self.pinch_target[0], game_time)
                        else:
                            fast_to_pos(left, self.pinch_target[0])

                        # Some rendering.
                        draw.draw_string_2d(
                            10, 70, 2, 2, f'Right going: {right.going}', draw.white())
                        draw.draw_string_2d(
                            10, 100, 2, 2, f'Left going: {left.going}', draw.white())

            else:
                draw.draw_string_2d(
                    10, 10, 2, 2, 'This example version has only been coded for 2 HiveBots.', draw.red())

            # Use this to send the drone inputs to the drones.
            for drone in self.drones:
                self.game_interface.update_player_input(
                    drone.ctrl, drone.index)

            # Some example rendering:
            draw.draw_string_2d(10, 10, 3, 3, f'{self.state}', draw.pink())
            # Renders ball prediction
            path = [step.physics.location for step in ball_prediction.slices[::10]]
            draw.draw_polyline_3d(path, draw.pink())

            # Renders drone indices.
            for drone in self.drones:
                draw.draw_string_3d(drone.pos, 1, 1, str(
                    drone.index), draw.white())

            # Team pinch info.
            if self.pinch_target is not None:
                draw.draw_rect_3d(
                    self.pinch_target[0], 10, 10, True, draw.red())

            # Ending rendering.
            draw.end_rendering()

            # Rate limit sleep.
            rate_limit.acquire()

# -----------------------------------------------------------

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

class Drone:
    """Houses the processed data from the packet for the drones.

    Attributes:
        index {int} -- The car's index in the packet.
        team {int} -- 0 if blue, else 1.
        pos {np.ndarray} -- Position vector.
        rot {np.ndarray} -- Rotation (pitch, yaw, roll).
        vel {np.ndarray} -- Velocity vector.
        boost {float} -- How much boost the car has.
        orient_m {np.ndarray} -- Orientation matrix.
        ctrl {PlayerInput} -- The controls we want to send to the drone.
        forward {bool} -- True if in the forward phase of turn_to_pos.
        going {bool} -- True if started going at the ball to pinch.
    """
    __slots__ = [
        'index',
        'team',
        'pos',
        'rot',
        'vel',
        'boost',
        'orient_m',
        'ctrl',
        'forward',
        'going'
    ]

    def __init__(self, index: int, team: int):
        self.index: int = index
        self.team: int = team
        self.pos: np.ndarray = np.zeros(3)
        self.rot: np.ndarray = np.zeros(3)
        self.vel: np.ndarray = np.zeros(3)
        self.boost: float = 0.0
        self.orient_m: np.ndarray = np.identity(3)
        self.ctrl: PlayerInput = PlayerInput()
        self.forward: bool = True
        self.going: bool = False


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


# An example state enum.
# Since you are using a hivemind it's as if
# all of your bots knew each other's state.
class State:
    SETUP = 'SETUP'
    WAIT = 'WAIT'
    PINCH = 'PINCH'

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
