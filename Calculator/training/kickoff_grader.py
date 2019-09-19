from dataclasses import dataclass
from math import sqrt
from typing import Optional, Union

from rlbot.training.training import Pass, Grade

from rlbottraining.common_graders.compound_grader import CompoundGrader
from rlbottraining.grading.grader import Grader

from rlbottraining.common_graders.timeout import FailOnTimeout
from rlbottraining.grading.training_tick_packet import TrainingTickPacket

@dataclass
class KickoffGrader(CompoundGrader):

    def __init__(self, timeout_seconds = 4.5, min_exercise_duration = 4, min_ball_displacement = 100):
        super().__init__([
            PassOnBallMoveFromKickoff(min_exercise_duration, min_ball_displacement),
            FailOnTimeout(timeout_seconds)
        ])


@dataclass
class PassOnBallMoveFromKickoff(Grader):
    min_exercise_duration : Union[int, float]
    min_ball_displacement : Union[int, float]
    initial_seconds_elapsed : type(None) = None
    ball_moved_flag : bool = False
    class PassDueToMovedBall(Pass):
        def __repr__(self):
            return f'{super().__repr__()}: Ball has moved from the start position.'

    def on_tick(self, tick: TrainingTickPacket) -> Optional[Grade]:

        packet = tick.game_tick_packet
        game_time = packet.game_info.seconds_elapsed
        ball = packet.game_ball.physics.location

        if self.initial_seconds_elapsed is None:
            self.initial_seconds_elapsed = game_time

        ball_moved = sqrt(ball.x**2 + ball.y**2 + (ball.z-93)**2) >= self.min_ball_displacement
        min_exercise_duration_reached = game_time >= self.initial_seconds_elapsed + self.min_exercise_duration

        if ball_moved and not self.ball_moved_flag:
            self.ball_moved_flag = True

        if self.ball_moved_flag and min_exercise_duration_reached:
            return self.PassDueToMovedBall()
        else:
            return None
