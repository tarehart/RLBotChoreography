from dataclasses import dataclass, field
from math import pi
from pathlib import Path
from typing import List, Tuple

from rlbot.matchconfig.match_config import MatchConfig, PlayerConfig, Team
from rlbot.utils.game_state_util import BallState, CarState, GameState, Physics, Rotator, Vector3

from kickoff_grader import QuickResetKickoffGrader
from rlbottraining.grading.grader import Grader
from rlbottraining.match_configs import make_empty_match_config
from rlbottraining.paths import BotConfigs
from rlbottraining.rng import SeededRandomNumberGenerator
from rlbottraining.training_exercise import TrainingExercise, Playlist


@dataclass
class SpawnLocation:
    pos: Vector3
    rot: Rotator


class Spawns():
    """Default Kickoffs Spawns (BLUE)"""
    CORNER_R = SpawnLocation(Vector3(-2048, -2560, 18), Rotator(0, 0.25*pi, 0))
    CORNER_L = SpawnLocation(Vector3(2048, -2560, 18), Rotator(0, 0.75*pi, 0))
    BACK_R = SpawnLocation(Vector3(-256, -3840, 18), Rotator(0, 0.5*pi, 0))
    BACK_L = SpawnLocation(Vector3(256.0, -3840, 18), Rotator(0, 0.5*pi, 0))
    STRAIGHT = SpawnLocation(Vector3(0, -4608, 18), Rotator(0, 0.5*pi, 0))


@dataclass
class KickoffExercise(TrainingExercise):
    grader: Grader = field(default_factory=QuickResetKickoffGrader)
    spawns: List[SpawnLocation] = field(default_factory=list)

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:

        num_players = self.match_config.num_players
        assert num_players == len(self.spawns), 'Number of players does not match the number of spawns.'

        car_states = {}
        for index in range(num_players):
            car_states[index] = CarState(
                boost_amount=33,
                physics=Physics(
                    location=self.spawns[index].pos,
                    velocity=Vector3(0, 0, 0),
                    rotation=self.spawns[index].rot,
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


def make_default_playlist() -> Playlist:

    # Choose which spawns you want to test.
    # The length of spawns should match the number of players in the match_config.

    exercises = [
        #KickoffExercise('Both Corners', spawns=[Spawns.CORNER_R, Spawns.CORNER_L]),
        KickoffExercise('Right Corner', spawns=[Spawns.CORNER_R]),
        KickoffExercise('Left Corner', spawns=[Spawns.CORNER_L]),
        KickoffExercise('Back Right', spawns=[Spawns.BACK_R]),
        KickoffExercise('Back Left', spawns=[Spawns.BACK_L]),
        KickoffExercise('Straight', spawns=[Spawns.STRAIGHT]),
    ]

    for ex in exercises:
        ex.match_config.player_configs = [
            # Replace with path to your bot.
            PlayerConfig.bot_config(BotConfigs.simple_bot, Team.BLUE) for _ in ex.spawns
        ]

    return exercises
