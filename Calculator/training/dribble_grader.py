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
    
    def __init__(self, timeout_seconds = 30, ally_team = 0):
        super().__init__([
            PassOnGoalForAllyTeam(ally_team),
            FailOnTimeout(timeout_seconds),
            FailOnDropBallNotNearGoal(),
        ])

@dataclass
class FailOnDropBallNotNearGoal(Grader):

    def __init__(self):
        super().__init__()
        self.dribble_started = False

    class FailDueToDroppedBall(Fail):
        def __repr__(self):
            return f'{super().__repr__()}: Ball dropped during dribble.'

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:

        packet = tick.game_tick_packet
        ball = packet.game_ball.physics.location

        if not self.dribble_started and ball.z > 150:
            self.dribble_started = True

        goal = Vector3(0,5120,100)

        distance_to_goal = ((ball.x - goal.x)**2 + (ball.y - goal.y)**2)**0.5

        # If the ball touches the ground not close to the goal.
        if self.dribble_started and ball.z < 100 and distance_to_goal > 1250 and ball.x != 0:
            return self.FailDueToDroppedBall()
        else:
            return None