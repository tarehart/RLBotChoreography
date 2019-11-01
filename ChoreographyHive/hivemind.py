'''The Hivemind'''

from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.game_interface import GameInterface

import time
import sys
from pathlib import Path

sys.path.append(Path(__file__).resolve().parent)

# Importing the chosen choreography:
# from choreography.lightfall_choreography import LightfallChoreography
# from choreography.crossing_squares import CrossingSquares
from choreography.boids import Boids
from choreography.drone import Drone


class Hivemind:
    """
    Sends and receives data from Rocket League, and maintains the list of drones.
    """

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

        self.drones = []

        # The chosen choreoraphy to perform.
        # TODO Set this based on input so it is easy to test different choreographies.
        self.choreo = Boids(self.game_interface) # TODO Set this within GUI
        self.choreo.generate_sequence()

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

        # Initialise drones list. Will be filled with Drone objects for every drone.
        self.drones = []

        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()

    def game_loop(self):

        # Creating packet which will be updated every tick.
        packet = GameTickPacket()

        # Nicknames the renderer to shorten code.
        draw = self.game_interface.renderer

        # MAIN LOOP:
        while self.loop_check():

            prev_time = packet.game_info.seconds_elapsed
            # Updating the game tick packet.
            self.game_interface.update_live_data_packet(packet)

            # Checking if packet is new, otherwise sleep.
            if prev_time == packet.game_info.seconds_elapsed:
                time.sleep(0.001)

            else:

                # Create a Drone object for every drone that holds its information.
                if packet.num_cars > len(self.drones):
                    # Clears the list if there are more cars than drones.
                    self.drones.clear()
                    for index in range(packet.num_cars):
                        self.drones.append(Drone(index, packet.game_cars[index].team))

                # Processing drone data.
                for drone in self.drones:
                    drone.update(packet.game_cars[drone.index])

                # Steps through the choreography.
                self.choreo.step(packet, self.drones)

                # Resets choreography once it has finished.
                if self.choreo.finished:
                    self.choreo = Boids(self.game_interface) # TODO Set this within GUI
                    self.choreo.generate_sequence()

                # Sends the drone inputs to the drones.
                for drone in self.drones:
                    self.game_interface.update_player_input(
                        convert_player_input(drone.ctrl), drone.index)

                # Some example endering:

                # draw.begin_rendering('Hivemind')
                # Renders drone indices.
                # for drone in self.drones:
                #     draw.draw_string_3d(drone.pos, 1, 1, str(
                #         drone.index), draw.white())
                # draw.end_rendering()

    def loop_check():
        """
        Checks whether the hivemind should keep looping or should die.
        """
        # TODO Check if should die here.
        return True


def convert_player_input(ctrl: SimpleControllerState) -> PlayerInput:
    """
    Converts a SimpleControllerState to a PlayerInput object.
    """
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
