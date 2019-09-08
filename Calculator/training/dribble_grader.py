from dataclasses import dataclass
from typing import Optional

from rlbot.training.training import Pass, Fail, Grade
from rlbot.utils.game_state_util import Vector3

from rlbottraining.grading.grader import Grader
from rlbottraining.common_graders.compound_grader import CompoundGrader
from rlbottraining.common_graders.goal_grader import PassOnGoalForAllyTeam
from rlbottraining.common_graders.timeout import FailOnTimeout
from rlbottraining.grading.training_tick_packet import TrainingTickPacket

@dataclass
class DribbleGrader(CompoundGrader):
    def __init__(self, ally_team = 0, timeout_seconds = 60):
        super().__init__([
            PassOnGoalForAllyTeam(ally_team),
            FailOnTimeout(timeout_seconds),
            FailOnDroppedBallOutsideGoalZone()
        ])

@dataclass
class FailOnDroppedBallOutsideGoalZone(Grader):

    class FailDueToDroppedBall(Fail):
        def __repr__(self):
            return f'{super().__repr__()}: Ball dropped during dribble.'

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:
        packet = tick.game_tick_packet
        ball = packet.game_ball.physics.location
        goal = Vector3(0,5120,100)

        distance_to_goal = ((ball.x - goal.x)**2 + (ball.y - goal.y)**2)**0.5

        # If the ball touches the ground, fail.
        if ball.z < 100 and distance_to_goal > 2000:
            return self.FailDueToDroppedBall()
        else:
            return None