'''Main bot file.'''

# RLBot imports
from rlbot.agents.base_agent                    import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct    import GameTickPacket
from rlbot.botmanager.helper_process_request    import HelperProcessRequest

# Other imports
import os
from multiprocessing import Queue

# File imports
import data

# Agent class
class Drone(BaseAgent):

    def __init__(self, *args):
        self.communication = Queue()

    def initialize_agent(self):

        self.ctrl = SimpleControllerState()
        data.init(self)

    def get_helper_process_request(self) -> HelperProcessRequest:

        filepath = os.path.join(os.path.dirname(__file__), 'hivemind.py')
        key = 'Hivemind'

        request = HelperProcessRequest(filepath, key)
        request.communication = self.communication
        return request

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        test = self.communication.get()
        print(self.drone_index,test)

        data.process(self, packet)
        self.ctrl.throttle = 1.0

        return self.ctrl