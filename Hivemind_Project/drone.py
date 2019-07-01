# RLBot imports
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.botmanager.bot_helper_process import BotHelperProcess

# File Imports
from hivemind import Hivemind

# Agent class
class Drone(BaseAgent):

    def initialize_agent(self):
        Hivemind(BotHelperProcess)
        self.ctrl = SimpleControllerState()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        return self.ctrl
