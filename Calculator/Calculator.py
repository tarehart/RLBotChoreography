#RLBot imports
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats

#Bot file imports
import Data, Brain, Exec, Render

class Calculator(BaseAgent):

    def initialize_agent(self):
        Data.init(self, SimpleControllerState())

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        Data.process(self, packet)
        Brain.think(self)
        Exec.actions(self)
        Render.all(self)
        return self.ctrl

#https://discordapp.com/channels/348658686962696195/348661571297214465/555450647806214164