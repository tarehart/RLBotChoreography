'''Main bot file.'''

# RLBot imports
from rlbot.agents.base_agent                    import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct    import GameTickPacket
from rlbot.botmanager.helper_process_request    import HelperProcessRequest

# Other imports
import os

# File imports
import data

# Agent class
class Drone(BaseAgent):

    def get_helper_process_request(self) -> HelperProcessRequest:
        filepath = os.path.join(os.path.dirname(__file__), 'hivemind.py')
        key = 'my_hivemind'
        options = {'port':240}
        request = HelperProcessRequest(filepath, key, None, options)
        return request

    def initialize_agent(self):
        self.ctrl = SimpleControllerState()
        data.init(self)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        data.process(self, packet)
        self.ctrl.throttle = 1.0
        return self.ctrl
