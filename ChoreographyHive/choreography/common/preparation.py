from typing import List

from rlbot.utils.game_state_util import CarState, Vector3, Rotator, Physics, GameState, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from choreography.drone import Drone
from choreography.group_step import GroupStep, StepResult
from hivemind import Hivemind


class HideBall(GroupStep):
    def __init__(self, z=3000):
        self.z = z

    def perform(self, packet, drones) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        Hivemind.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, self.z),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)


class LetAllCarsSpawn(GroupStep):
    def __init__(self, expected_num: float):
        self.expected_num = expected_num
        self.start_time = None

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:
        if not self.start_time:
            self.start_time = packet.game_info.seconds_elapsed

        fully_spawned = len(drones) >= self.expected_num and packet.game_info.is_round_active
        elapsed = packet.game_info.seconds_elapsed - self.start_time
        if not fully_spawned:
            start_x = -4000
            y_increment = 100
            start_y = -4000
            start_z = 40
            car_states = {}
            for drone in drones:
                car_states[drone.index] = CarState(
                    Physics(location=Vector3(start_x, start_y + drone.index * y_increment, start_z),
                            velocity=Vector3(0, 0, 0),
                            rotation=Rotator(0, 0, 0)))
            Hivemind.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=fully_spawned or elapsed > 30)
