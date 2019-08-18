from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from zeroG import microgravity

class TestBot(BaseAgent):

    def initialize_agent(self):
        """This runs once before the bot starts up. Initialises attributes."""

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """Runs every tick. Returns the bot controller.
        
        Arguments:
            packet {GameTickPacket} -- The information packet from the game.
        
        Returns:
            SimpleControllerState -- The controller for the bot.
        """

        microgravity(self, packet)

        return SimpleControllerState()