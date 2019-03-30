#RLBot imports
from rlbot.agents.base_agent                    import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct    import GameTickPacket
from rlbot.utils.structures.quick_chats         import QuickChats
#from rlbot.agents.human.controller_input        import controller


#Bot file imports
import Data, Brain, Exec, Render

class Calculator(BaseAgent):

    def initialize_agent(self):
        self.ctrl = SimpleControllerState()
        Data.init(self)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        Data.process(self, packet)
        Brain.think(self)
        Render.everything(self)
        return Exec.actions(self)