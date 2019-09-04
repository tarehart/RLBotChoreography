'''Main bot file.'''

# RLBot imports.
from rlbot.agents.base_agent                    import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct    import GameTickPacket

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

# Local file imports.
import data
from utils import np, a3l, normalise, local, cap, team_sign, special_sauce
from states import Idle, Catch

class Calculator(BaseAgent):

    def initialize_agent(self):
        self.need_setup = True
        self.state = Idle()

    def checkState(self):
        if self.state.expired:
            if Catch.available(self):
                self.state = Catch()
            else:
                Idle()
        
    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        # Runs setup.
        if self.need_setup:
            field_info = self.get_field_info()
            data.setup(self, packet, field_info)
            self.need_setup = False

        # Preprocessing.
        data.process(self, packet)
        self.ctrl = SimpleControllerState()

        # Handle states.
        self.checkState()

        # Execute state.
        if not self.state.expired:
            self.state.execute(self)

        # Render.
        self.render(self.renderer)

        return self.ctrl 


    def render(self, r):
        r.begin_rendering()
        r.draw_string_2d(10, 10, 2, 2, f'{self.state.__class__.__name__}', r.white())
        r.end_rendering()