from dataclasses import dataclass
from typing import Optional

from rlbot.training.training import Pass, Grade

from rlbottraining.grading.grader import Grader
from rlbottraining.common_graders.compound_grader import CompoundGrader

from rlbottraining.common_graders.timeout import FailOnTimeout
from rlbottraining.grading.training_tick_packet import TrainingTickPacket

@dataclass
class QuickResetKickoffGrader(CompoundGrader):

    def __init__(self, timeout_seconds = 5):
        super().__init__([
            PassOnBallMoveFromKickoff(),
            FailOnTimeout(timeout_seconds)
        ])


@dataclass
class PassOnBallMoveFromKickoff(Grader):

    class PassDueToMovedBall(Pass):
        def __repr__(self):
            return f'{super().__repr__()}: Ball has moved from the start position.'

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:

        ball = tick.game_tick_packet.game_ball.physics.location

        if  -100 > ball.x or ball.x > 100 or -100 > ball.y or ball.y > 100:
            return self.PassDueToMovedBall()
        else:
            return None
