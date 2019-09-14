from dataclasses import dataclass
from pathlib import Path
from math import pi

from kickoff_grader import QuickResetKickoffGrader

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.matchconfig.match_config import Team, PlayerConfig

from rlbottraining.training_exercise import TrainingExercise, Playlist
from rlbottraining.rng import SeededRandomNumberGenerator


@dataclass
class KickoffType:
    pos: Vector3
    rot: Rotator


right_corner = KickoffType(Vector3(-2048, -2560, 18), Rotator(0, 0.25*pi, 0))
left_corner = KickoffType(Vector3(2048, -2560, 18), Rotator(0, 0.75*pi, 0))
back_right = KickoffType(Vector3(-256, -3840, 18), Rotator(0, 0.5*pi, 0))
back_left = KickoffType(Vector3(256.0, -3840, 18), Rotator(0, 0.5*pi, 0))
straight = KickoffType(Vector3(0, -4608, 18), Rotator(0, 0.5*pi, 0))


class KickoffExercise(TrainingExercise):

    def __init__(self, name, kickoff_type):
        super().__init__(name, grader=QuickResetKickoffGrader())
        self.kickoff_type: KickoffType = kickoff_type

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        kickoff_position = self.kickoff_type.pos
        kickoff_rotation = self.kickoff_type.rot

        car_state = CarState(
            boost_amount=33,
            physics=Physics(
                location=kickoff_position,
                velocity=Vector3(0, 0, 0),
                rotation=kickoff_rotation,
                angular_velocity=Vector3(0, 0, 0)
            )
        )

        ball_state = BallState(
            Physics(
                location=Vector3(0, 0, 93),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)
            )
        )

        game_state = GameState(ball=ball_state, cars={0: car_state})
        return game_state


def make_default_playlist() -> Playlist:
    exercises = [
        KickoffExercise(name='Right Corner', kickoff_type=right_corner),
        KickoffExercise(name='Left Corner', kickoff_type=left_corner),
        KickoffExercise(name='Back Right', kickoff_type=back_right),
        KickoffExercise(name='Back Left', kickoff_type=back_left),
        KickoffExercise(name='Straight', kickoff_type=straight),
    ]

    for ex in exercises:
        ex.match_config.player_configs = [
            PlayerConfig.bot_config(Path(__file__).absolute(
            ).parent.parent / 'Calculator.cfg', Team.BLUE)
        ]

    return exercises
