from typing import Callable, List

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import ChoreographyBase
from choreography.drone import Drone


class StepResult:
    def __init__(self, finished: bool = False):
        self.finished = finished


class GroupStep:
    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:
        pass


class DroneListStep(GroupStep):
    """
    Takes a function that receives the entire drone list. More powerful but less
    convenient than PerDroneStep. It should be possible to accomplish almost anything
    with this one.
    """
    def __init__(self, fn: Callable[[GameTickPacket, List[Drone], float], StepResult], time_offset: float = 0):
        self.fn = fn
        self.start_time = None
        self.time_offset = time_offset

    def perform(self, packet, drones):
        if not self.start_time:
            self.start_time = packet.game_info.seconds_elapsed + self.time_offset
        return self.fn(packet, drones, self.start_time)


class PerDroneStep(GroupStep):
    """
    Takes a function and applies it to every drone individually. They can still behave differently
    because you have access to the drone's index, position, velocity, etc.
    """
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


class BlindBehaviorStep(PerDroneStep):
    """
    For every drone in the list, output the given controls for the specified duration.
    For example you could make everyone to boost simultaneously for .5 seconds.
    """
    def __init__(self, controls: SimpleControllerState, duration: float):
        super().__init__(self.blind, duration)
        self.controls = controls

    def blind(self, packet: GameTickPacket, drone: Drone, elapsed: float):
        drone.ctrl = self.controls
        return StepResult(finished=False)


class SubGroupChoreography(ChoreographyBase):
    """
    This defines a sub-group of drones that may behave differently from the other drones present
    on the field.
    """
    def __init__(self, drones: List[Drone], start_time: float):
        super().__init__()
        self.drones = drones
        self.start_time = start_time

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        for drone in self.drones:  # Only reset your OWN drones.
            drone.reset_ctrl()


class SubGroupChoreographySettable(SubGroupChoreography):
    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface


class SubGroupOrchestrator(GroupStep):
    def __init__(self, group_list: List[SubGroupChoreography], max_duration = None):
        self.group_list = group_list
        self.active_groups: List[SubGroupChoreography] = []
        self.completed = False
        self.group_list.sort(key=lambda x: x.start_time)
        self.start_time = None
        self.max_duration = max_duration

    def update(self, current_time):
        if not self.start_time:
            self.start_time = current_time

        if len(self.group_list) == 0 and len(self.active_groups) == 0:
            self.completed = True
            return
        self.active_groups = [g for g in self.active_groups if not g.finished]
        num_consumed = 0
        elapsed_time = current_time - self.start_time
        if self.max_duration is not None and elapsed_time > self.max_duration:
            self.completed = True
            return

        for candidate in self.group_list:
            if candidate.start_time > elapsed_time:
                break
            candidate.generate_sequence(candidate.drones)
            self.active_groups.append(candidate)
            num_consumed += 1

        self.group_list = self.group_list[num_consumed:]

    def step(self, packet: GameTickPacket):
        for choreo in self.active_groups:
            # Pass the choreo its own drones. Don't make it aware of all the drones in the match.
            choreo.step(packet, choreo.drones)

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:
        self.update(packet.game_info.seconds_elapsed)
        self.step(packet)
        return StepResult(finished=self.completed)
