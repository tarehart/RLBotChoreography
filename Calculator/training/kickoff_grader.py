from dataclasses import dataclass
from typing import Optional

from rlbot.training.training import Pass, Grade

from rlbottraining.grading.grader import Grader
from rlbottraining.common_graders.compound_grader import CompoundGrader

from rlbottraining.common_graders.timeout import FailOnTimeout
from rlbottraining.grading.training_tick_packet import TrainingTickPacket

@dataclass
class QuickResetKickoffGrader(CompoundGrader):

    def __init__(self, timeout_seconds = 5.5, reset_time = 5):
        super().__init__([
            PassOnBallMoveFromKickoff(reset_time),
            FailOnTimeout(timeout_seconds)
        ])


@dataclass
class PassOnBallMoveFromKickoff(Grader):

    def __init__(self, reset_time):
        self.reset_time = reset_time
        self.initial_seconds_elapsed = None


    class PassDueToMovedBall(Pass):
        def __repr__(self):
            return f'{super().__repr__()}: Ball has moved from the start position.'

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:

        packet = tick.game_tick_packet
        game_time = packet.game_info.seconds_elapsed
        ball = packet.game_ball.physics.location

        if self.initial_seconds_elapsed is None:
            self.initial_seconds_elapsed = game_time

        ball_out_of_centre = -100 > ball.x or ball.x > 100 or -100 > ball.y or ball.y > 100
        reset_time_reached = game_time >= self.initial_seconds_elapsed + self.reset_time
        if ball_out_of_centre and reset_time_reached:
            return self.PassDueToMovedBall()
        else:
            return None
