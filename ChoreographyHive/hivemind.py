'''The Hivemind'''

from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.game_interface import GameInterface

import time

from choreography.drone import Drone
from queue_commands import QCommand

class Hivemind:
    """
    Sends and receives data from Rocket League, and maintains the list of drones.
    """

    # Some terminology:
    # hivemind = the process which controls the drones.
    # drone = a bot under the hivemind's control.

    def __init__(self, queue, choreo_obj):
        # Sets up the logger. The string is the name of your hivemind.
        # Call this something unique so people can differentiate between hiveminds.
        self.logger = get_logger('Choreography Hivemind')

        # The game interface is how you get access to things
        # like ball prediction, the game tick packet, or rendering.
        self.game_interface = GameInterface(self.logger)

        self.drones = []

        self.choreo = choreo_obj(self.game_interface)
        self.choreo.generate_sequence()

        # Set up queue to know when to stop and reload.
        self.queue = queue

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

        # MAIN LOOP:
        while self.loop_check():
            #print('test')

            prev_time = packet.game_info.seconds_elapsed
            # Updating the game tick packet.
            self.game_interface.update_live_data_packet(packet)

            # Checking if packet is new, otherwise sleep.
            if prev_time == packet.game_info.seconds_elapsed:
                time.sleep(0.001)
                continue

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
                # Re-instantiates the choreography.
                self.choreo = self.choreo.__class__(self.game_interface)
                self.choreo.generate_sequence()

            # Sends the drone inputs to the drones.
            for drone in self.drones:
                self.game_interface.update_player_input(
                    convert_player_input(drone.ctrl), drone.index)

    def loop_check(self):
        """
        Checks whether the hivemind should keep looping or should die.
        """
        if self.queue.empty():
            return True
            
        else:
            message = self.queue.get()
            return message != QCommand.STOP


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
