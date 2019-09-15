from dataclasses import dataclass
from pathlib import Path
from math import pi

from kickoff_grader import QuickResetKickoffGrader

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.matchconfig.match_config import Team, PlayerConfig

from rlbottraining.training_exercise import TrainingExercise, Playlist
from rlbottraining.rng import SeededRandomNumberGenerator


class KickoffExercise(TrainingExercise):

    def __init__(self, name, kickoffs):
        super().__init__(name, grader=QuickResetKickoffGrader())
        self.kickoffs = kickoffs

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        car_states = {}
        for index in range(len(self.kickoffs)):
            car_states[index] = CarState(
                boost_amount=33,
                physics=Physics(
                    location=self.kickoffs[index].pos,
                    velocity=Vector3(0, 0, 0),
                    rotation=self.kickoffs[index].rot,
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

        game_state = GameState(ball=ball_state, cars=car_states)
        return game_state


@dataclass
class KickoffType:
    pos: Vector3
    rot: Rotator

# Default kickoffs.
right_corner = KickoffType(Vector3(-2048, -2560, 18), Rotator(0, 0.25*pi, 0))
left_corner = KickoffType(Vector3(2048, -2560, 18), Rotator(0, 0.75*pi, 0))
back_right = KickoffType(Vector3(-256, -3840, 18), Rotator(0, 0.5*pi, 0))
back_left = KickoffType(Vector3(256.0, -3840, 18), Rotator(0, 0.5*pi, 0))
straight = KickoffType(Vector3(0, -4608, 18), Rotator(0, 0.5*pi, 0))


def make_default_playlist() -> Playlist:

    # Choose which kickoffs you want to test. 
    # The length of kickoffs should match the number of players in the match_config.

    exercises = [
        KickoffExercise(name='Both Corners', kickoffs=(right_corner,left_corner)),
        #KickoffExercise(name='Right Corner', kickoffs=(right_corner,))
        #KickoffExercise(name='Left Corner', kickoffs=(left_corner,)),
        #KickoffExercise(name='Back Right', kickoffs=(back_right,)),
        #KickoffExercise(name='Back Left', kickoffs=(back_left,)),
        #KickoffExercise(name='Straight', kickoffs=(straight,)),
    ]

    for ex in exercises:
        ex.match_config.player_configs = [
            PlayerConfig.bot_config(Path(__file__).absolute().parent.parent / 'Calculator.cfg', Team.BLUE),
            PlayerConfig.bot_config(Path(__file__).absolute().parent.parent / 'Calculator.cfg', Team.BLUE),
        ]

    return exercises
