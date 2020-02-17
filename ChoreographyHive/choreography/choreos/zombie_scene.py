import math
from random import random
from typing import List

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import Aerial, vec3
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone, slow_to_pos, a3v
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, SubGroupChoreography, \
    SubGroupOrchestrator, GroupStep, PerDroneStep
from util.orientation import look_at_orientation
from util.vec import Vec3

BASE_CAR_Z = 17


def stagger(n):
    return (n % 2) * 2 - 1


class FlyingDuo(SubGroupChoreography):

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.pose_drones))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 0.6))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, jump=True, pitch=0.7), 0.3))
        self.sequence.append(PerDroneStep(self.duo_roll, 2))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 3))

    def duo_roll(self, packet, drone: Drone, start_time) -> StepResult:
        roll_direction = stagger(drone.index)
        drone.ctrl.roll = roll_direction * 0.3
        drone.ctrl.yaw = roll_direction * 0.1
        drone.ctrl.boost = True
        return StepResult(finished=False)

    def pose_drones(self, packet, drones, start_time) -> StepResult:
        pose_duo(drones, self.game_interface)
        return StepResult(finished=True)

def pose_duo(drones, game_interface):
    car_states = {}
    drones_per_row = 2
    for index, drone in enumerate(drones):
        row = index // drones_per_row
        column = index % drones_per_row
        x_value = stagger(column) * 150
        y_value = row * -300 - 4000
        yaw_tweak = stagger(index) * -0.06
        car_states[drone.index] = CarState(
            Physics(location=Vector3(x_value, y_value, 40),
                    velocity=Vector3(0, 0, 0),
                    angular_velocity=Vector3(0, 0, 0),
                    rotation=Rotator(0, math.pi / 2 + yaw_tweak, 0)))
    game_interface.set_game_state(GameState(cars=car_states))


def unit_random():
    return random() * 2 - 1

class LineUpZombies(SubGroupChoreography):

    def __init__(self, drones: List[Drone], start_time: float, game_interface):
        super().__init__(drones, start_time)
        self.game_interface = game_interface

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.line_up))

    def line_up(self, packet, drones: List[Drone], start_time) -> StepResult:
        car_states = {}
        for index, drone in enumerate(drones):
            x_value = stagger(index) * 1000 + unit_random() * 300
            y_value = index * 92 - 896 + unit_random() * 100
            car_states[drone.index] = CarState(
                Physics(location=Vector3(x_value, y_value, 40),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, math.pi / 2 + stagger(index) * math.pi / 2, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

class RunZombies(SubGroupChoreography):

    def __init__(self, drones: List[Drone], start_time: float, game_info: GameInfo):
        super().__init__(drones, start_time)
        self.game_info = game_info
        self.aerials: List[Aerial] = []

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        pass

    def get_target_vec(self, packet, drone):
        target_index = drone.index % 2
        target_car = packet.game_cars[target_index]
        target_now = a3v(target_car.physics.location)
        return target_now + a3v(target_car.physics.velocity) * 1.5

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(PerDroneStep(self.wander, 3))
        self.sequence.append(PerDroneStep(self.get_brains, 0.5))
        self.sequence.append(DroneListStep(self.get_air))

    def wander(self, packet, drone, start_time) -> StepResult:
        drone.ctrl.throttle = 0.07
        if random() > .95:
            drone.ctrl.steer = unit_random()
        return StepResult()

    def get_brains(self, packet: GameTickPacket, drone: Drone, start_time) -> StepResult:
        target_future = self.get_target_vec(packet, drone)
        slow_to_pos(drone, target_future)
        drone.ctrl.boost = False
        drone.ctrl.throttle = min(drone.ctrl.throttle, 0.3)
        return StepResult()

    def get_air(self, packet: GameTickPacket, drones: List[Drone], start_time) -> StepResult:

        if len(self.aerials) == 0:
            for drone in drones:
                target_future = self.get_target_vec(packet, drone)
                aerial = Aerial(self.game_info.cars[drone.index],
                                vec3(target_future[0], target_future[1], target_future[2]), 1)
                self.aerials.append(aerial)

        for index, drone in enumerate(drones):
            aerial = self.aerials[index]
            aerial.step(0.008)
            drone.ctrl.boost = aerial.controls.boost
            drone.ctrl.pitch = aerial.controls.pitch
            drone.ctrl.yaw = aerial.controls.yaw
            drone.ctrl.roll = aerial.controls.roll
            drone.ctrl.jump = aerial.controls.jump

        elapsed = packet.game_info.seconds_elapsed - start_time
        return StepResult(finished=elapsed > 0.9)


class ZombieScene(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.game_info = GameInfo(0, 0)

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        self.game_info.read_packet(packet)

    @staticmethod
    def get_num_bots():
        return 10

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(HideBall())

        if len(drones) < self.get_num_bots():
            return

        group_list = [
            FlyingDuo(game_interface=self.game_interface, drones=drones[:2], start_time=2),
            LineUpZombies(drones=drones[2:], start_time=0, game_interface=self.game_interface),
            RunZombies(drones=drones[2:], start_time=0, game_info=self.game_info)
        ]

        self.sequence.append(SubGroupOrchestrator(group_list=group_list))

