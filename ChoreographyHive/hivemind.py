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

from choreography.lightfall_choreography import LightfallChoreography
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

        self.lightfall_choreography = LightfallChoreography(self.game_interface)
        self.lightfall_choreography.generate_sequence()

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
                draw.begin_rendering('Hivemind')

                # PRE-PROCESSING:

                # Create a Drone object for every drone that holds its information.
                if packet.num_cars > len(self.drones):
                    # Clears the list if there are more cars than drones.
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
