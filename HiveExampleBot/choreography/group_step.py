from typing import Callable, List

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from choreography.drone import Drone


class StepResult:
    def __init__(self, finished: bool = False):
        self.finished = finished


class GroupStep:
    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:
        pass


class LambdaStep(GroupStep):
    def __init__(self, fn: Callable[[GameTickPacket, List[Drone]], StepResult]):
        self.fn = fn

    def perform(self, packet, drones):
        return self.fn(packet, drones)


class SynchronizedBehaviorStep(GroupStep):
    def __init__(self, bot_fn: Callable[[GameTickPacket, Drone, float], StepResult], max_duration: float):
        self.bot_fn = bot_fn
        self.max_duration = max_duration
        self.start_time = None

    def perform(self, packet, drones: List[Drone]):
        if not self.start_time:
            self.start_time = packet.game_info.seconds_elapsed

        if packet.game_info.seconds_elapsed > self.start_time + self.max_duration:
            return StepResult(finished=True)

        finished = True
        for drone in drones:
            result = self.bot_fn(packet, drone, self.start_time)
            if not result.finished:
                finished = False
        return StepResult(finished=finished)


class BlindBehaviorStep(SynchronizedBehaviorStep):
    def __init__(self, controls: SimpleControllerState, duration: float):
        super().__init__(self.blind, duration)
        self.controls = controls

    def blind(self, packet: GameTickPacket, drone: Drone, elapsed: float):
        drone.ctrl = self.controls
        return StepResult(finished=False)
