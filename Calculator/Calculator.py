'''Main bot file.'''

# RLBot imports.
from rlbot.agents.base_agent                    import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct    import GameTickPacket

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

# Local file imports.
import data
from utils import np, a3l, normalise, local, cap, team_sign, special_sauce
###from states import Idle, Catch

class Calculator(BaseAgent):

    def initialize_agent(self):
        self.need_setup = True
        #self.state = Idle()

    def checkState(self):
        if self.state.expired:
            pass
            '''
            if Catch().available(self):
                self.state = Catch()
            else:
                self.state = Idle()
            '''
        
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
        ###self.checkState()

        # Execute states.
        ###self.state.execute(self)

        # Render.
        ###self.render(self.renderer)

        # Quick v0tzwei shooting just to enter into league play. Will be removed.
        goal = a3l([0, 5120, 0]) * team_sign(self.team)

        # Calculate distance to ball.
        distance = np.linalg.norm(self.ball.pos - self.player.pos)

        # Find directions based on where we want to hit the ball.
        direction_to_hit = normalise(goal - self.ball.pos)
        perpendicular_to_hit = np.cross(direction_to_hit, a3l([0,0,1]))

        # Calculating component lengths and multiplying with direction.
        perpendicular_component = perpendicular_to_hit * cap(np.dot(perpendicular_to_hit, self.ball.pos), -distance/8, distance/8)
        in_direction_component = -direction_to_hit * 2*distance/3

        # Combine components to get a drive target.
        drive_target = self.ball.pos + in_direction_component + perpendicular_component

        # Calculate angle
        local_target = local(self.player.orient_m, self.player.pos, drive_target)
        angle = np.arctan2(local_target[1], local_target[0])

        # Steer using special sauce.
        self.ctrl.steer = special_sauce(angle, -6)

        if abs(angle) < 0.3:
            self.ctrl.boost = True

        if abs(angle) > 1.6:
            self.ctrl.handbrake = True

        self.ctrl.throttle = 1

        return self.ctrl 


    def render(self, r):
        r.begin_rendering()
        r.draw_string_2d(10, 10, 2, 2, f'{self.state.__class__.__name__}', r.white())
        r.end_rendering()