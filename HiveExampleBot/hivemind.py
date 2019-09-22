'''The Hivemind'''
import os
import sys

from rlbot.utils.structures.bot_input_struct import PlayerInput

from choreography.lightfall_choreography import LightfallChoreography

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import time
import numpy as np
from rlbot.agents.base_agent import SimpleControllerState

from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.structures.game_interface import GameInterface

from choreography.drone import Drone

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


# Additional tweakable positions starting on line 187 for where bots will wait.
# More tweakable values directly in the controllers at the bottom.

# -----------------------------------------------------------

# THE HIVEMIND:

class ExampleHivemind:

    # Some terminology:
    # hivemind = the process which controls the drones.
    # drone = a bot under the hivemind's control.

    def __init__(self):
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

                # Create a Drone object for every drone that holds its information.
                if packet.num_cars > len(self.drones):
                    self.drones.clear()
                    for index in range(packet.num_cars):
                        self.drones.append(Drone(index, packet.game_cars[index].team))

                # Processing drone data.
                for drone in self.drones:
                    drone.update(packet.game_cars[drone.index])

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

# LINEAR ALGEBRA:
