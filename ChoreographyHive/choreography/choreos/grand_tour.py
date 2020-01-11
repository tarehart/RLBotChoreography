import math
from dataclasses import dataclass
from typing import List

from RLUtilities.GameInfo import GameInfo
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography, ChoreographyBase
from choreography.drone import Drone
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, GroupStep
from util.orientation import look_at_orientation
from util.vec import Vec3

BASE_CAR_Z = 17


class GroupChoreography(ChoreographyBase):
    """
    This defines a sub-group of drones that may behave differently from the other drones present
    on the field.
    """
    def __init__(self, drones: List[Drone], start_time: float):
        super().__init__()
        self.drones = drones
        self.start_time = start_time


class GroupOrchestrator(GroupStep):
    def __init__(self, group_list: List[GroupChoreography]):
        self.group_list = group_list
        self.active_groups: List[GroupChoreography] = []
        self.completed = False
        self.group_list.sort(key=lambda x: x.start_time)
        self.start_time = None

    def update(self, current_time):
        if not self.start_time:
            self.start_time = current_time

        if len(self.group_list) == 0 and len(self.active_groups) == 0:
            self.completed = True
            return
        self.active_groups = [g for g in self.active_groups if not g.finished]
        num_consumed = 0
        for candidate in self.group_list:
            if candidate.start_time <= current_time - self.start_time:
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


def stagger(n):
    return (n % 2) * 2 - 1


class CruiseFormation(GroupChoreography):

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.generate_sequence(drones)

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.pose_drones))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 0.5))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, steer=0.3), 0.7))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, steer=-0.3), 0.9))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(jump=True, boost=True, roll=-1.0, yaw=1.0), 1))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, pitch=0.6, yaw=-1.0), 0.2))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 0.3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0), 0.5))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 2))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, roll=1), 0.6))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, roll=-1), 0.1))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 1))

    def pose_drones(self, packet, global_drones, start_time) -> StepResult:
        car_states = {}
        drones_per_wing = 7
        for index, drone in enumerate(self.drones):
            wing = index // drones_per_wing
            wing_index = index % drones_per_wing
            rank = 0 if wing_index == 0 else (wing_index + 1) // 2
            x_value = stagger(wing_index) * rank * 150
            y_value = rank * -150 + wing * -300 - 4000
            car_states[drone.index] = CarState(
                Physics(location=Vector3(x_value, y_value, 40),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, math.pi / 2, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)


class FastFly(GroupChoreography):

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float, location: Vec3, direction: Vec3):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.location = location
        self.direction = direction
        self.generate_sequence(drones)

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.pose_drones))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 3))

    def pose_drones(self, packet, global_drones, start_time) -> StepResult:
        car_states = {}
        num_drones = len(self.drones)
        spacing = 75
        orientation = look_at_orientation(self.direction, Vec3(0, 1, 0))
        for index, drone in enumerate(self.drones):
            loc = self.location + orientation.right.rescale(index * spacing - num_drones * spacing / 2)
            car_states[drone.index] = CarState(
                Physics(location=Vector3(loc.x, loc.y, loc.z),
                        velocity=Vector3(self.direction.x, self.direction.y, self.direction.z),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=orientation.to_rotator()))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)


class GrandTourChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

        self.game_info = GameInfo(0, 0)
        self.renderer = self.game_interface.renderer

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()
        pause_time = 0.2

        self.sequence.append(DroneListStep(self.position_ball))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))

        if len(drones) < 48:
            return

        self.sequence.append(GroupOrchestrator(group_list=[
            CruiseFormation(game_interface=self.game_interface, drones=drones[:12], start_time=0),
            FastFly(game_interface=self.game_interface, drones=[drones[12], drones[15], drones[18], drones[21]],
                    start_time=1.2, location=Vec3(-2500, 0, 200), direction=Vec3(1000, 300, 500)),
            FastFly(game_interface=self.game_interface, drones=[drones[13], drones[16], drones[19], drones[22]],
                    start_time=1.5, location=Vec3(2500, 900, 200), direction=Vec3(-1000, 300, 500)),
            FastFly(game_interface=self.game_interface, drones=[drones[14], drones[17], drones[20], drones[23]],
                    start_time=1.8, location=Vec3(-2500, 1800, 200), direction=Vec3(1000, 300, 500))
        ]))

    def line_up(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """
        start_x = -2000
        y_increment = 100
        start_y = -len(drones) * y_increment / 2
        start_z = 40
        car_states = {}
        for drone in drones:
            car_states[drone.index] = CarState(
                Physics(location=Vector3(start_x, start_y + drone.index * y_increment, start_z),
                        velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def position_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(3000, -2200, 118),
            velocity=Vector3(0, 0, 0.00001),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
