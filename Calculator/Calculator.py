#RLBot imports
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats

#Bot file imports
import Data, Brain, Exec, Render

class Calculator(BaseAgent):

    def initialize_agent(self):
        Data.init(self, SimpleControllerState())
        #Render.init_colours(self)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        Data.process(self, packet)
        Brain.think(self)
        Exec.actions(self)
        if not self.m_ended and (self.ko_pause or self.r_active):
            Render.all(self)
        return self.ctrl