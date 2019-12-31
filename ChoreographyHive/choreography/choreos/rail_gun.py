import math
from typing import List

from RLUtilities.GameInfo import GameInfo
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.messages.flat.GameTickPacket import GameTickPacket
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import Drone
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, GroupStep

BASE_CAR_Z = 17


class RailGunSubChoreography(Choreography):

    def __init__(self, time_offset: float):
        super().__init__()
        self.time_offset = time_offset
        self.previous_seconds_elapsed = 0

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.wait_one, self.time_offset))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, boost=True), 1.8))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, jump=True, boost=True), .15))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, boost=True), .01))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, jump=True, boost=True, pitch=-1), .3))

    def wait_one(self, packet, drones, start_time):
        elapsed = packet.game_info.seconds_elapsed - start_time
        return StepResult(finished=elapsed >= 1)


# IMPULSE_DELAYS = [0, 0.05, 0.1, 0.11, 0.14, 0.17, 0.20, 0.22, 0.24]
IMPULSE_DELAYS = [math.sqrt((n + 1) * .008) + 0.008 * n for n in range(0, 48)]


class ImpulseOrchestratorStep(GroupStep):

    def __init__(self, game_interface: GameInterface, game_info: GameInfo):
        self.sub_choreographies: List[Choreography] = []
        self.game_interface = game_interface
        self.game_info = game_info
        self.drones_per_ring = 2

    def slice_drones(self, drones: List, index):
        return drones[index * self.drones_per_ring: (index + 1) * self.drones_per_ring]

    def get_impulse_delay(self, n):
        if n < len(IMPULSE_DELAYS):
            return IMPULSE_DELAYS[n]
        return 1

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:

        if len(drones) == 0:
            return StepResult(finished=True)

        if len(self.sub_choreographies) == 0:
            num_rings = len(drones) // self.drones_per_ring
            self.sub_choreographies = [RailGunSubChoreography(self.get_impulse_delay(n))
                                       for n in range(0, num_rings)]

            for index, sub_choreo in enumerate(self.sub_choreographies):
                sub_choreo.generate_sequence(self.slice_drones(drones, index))

        all_finished = True
        for index, sub_choreo in enumerate(self.sub_choreographies):
            sub_choreo.step(packet, self.slice_drones(drones, index))
            all_finished = all_finished and sub_choreo.finished

        return StepResult(finished=all_finished)


def stagger(n):
    return (n % 2) * 2 - 1


class RailGunChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

        self.game_info = GameInfo(0, 0)
        self.renderer = self.game_interface.renderer

    @staticmethod
    def get_num_bots():
        return 6

    def generate_sequence(self, drones):
        self.sequence.clear()
        pause_time = 0.2

        self.sequence.append(DroneListStep(self.position_ball))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(ImpulseOrchestratorStep(self.game_interface, self.game_info))

    def line_up(self, packet, drones, start_time) -> StepResult:
        car_states = {}
        for drone in drones:
            x_value = stagger(drone.index) * 3500
            car_states[drone.index] = CarState(
                Physics(location=Vector3(x_value, drone.index // 2 * 120 - 4000, 40),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, math.pi / 2 + stagger(drone.index) * 1.1, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def position_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, -2200, 118),
            velocity=Vector3(0, 0, 0.00001),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
