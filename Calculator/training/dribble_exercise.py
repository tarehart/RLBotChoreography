from dataclasses import dataclass, field
from pathlib import Path
from math import pi

from dribble_grader import DribbleGrader

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.matchconfig.match_config import Team, PlayerConfig 

from rlbottraining.training_exercise import TrainingExercise, Playlist
from rlbottraining.grading.grader import Grader
from rlbottraining.rng import SeededRandomNumberGenerator

@dataclass
class DribbleExercise(TrainingExercise):
    grader : Grader = field(default_factory=DribbleGrader)

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        car_state = CarState(
            boost_amount=100,
            physics=Physics(
                location=Vector3(0, -4000, 20),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, pi / 2, 0)
                )
            )

        ball_state = BallState(
            Physics(
                location=Vector3(0, -3500, 500),
                velocity=Vector3(0, 0, 1)
                )
            )

        game_state = GameState(ball=ball_state, cars={0: car_state})
        return game_state



def make_default_playlist() -> Playlist:
    ex = DribbleExercise('Simple Dribble')
    ex.match_config.player_configs = [
        PlayerConfig.bot_config(Path(__file__).absolute().parent.parent / 'Calculator.cfg', Team.BLUE)
    ]
    return [ex]






    