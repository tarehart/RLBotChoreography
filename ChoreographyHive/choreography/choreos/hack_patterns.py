import math
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import vec3, Aerial
from numpy.linalg import norm
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface
from scipy.spatial.transform import Rotation

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone, slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, GroupStep, SubGroupChoreography, \
    SubGroupOrchestrator
from util.orientation import look_at_orientation
from util.vec import Vec3

BASE_CAR_Z = 17


class AerialToLocation(GroupStep):
    def __init__(self, game_info: GameInfo, target: Vec3, duration: float):
        self.game_info = game_info
        self.target = target
        self.duration = duration
        self.aerials: List[Aerial] = []
        self.start_time = None

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:

        if self.start_time is None:
            self.start_time = packet.game_info.seconds_elapsed
            for index, drone in enumerate(drones):
                aerial = Aerial(self.game_info.cars[drone.index], vec3(0, 0, 0), 0)
                aerial.t_arrival = self.start_time + self.duration
                aerial.target = vec3(self.target.x, self.target.y, self.target.z)
                self.aerials.append(aerial)

        for index, drone in enumerate(drones):
            aerial = self.aerials[index]
            aerial.step(0.008)
            drone.ctrl.boost = aerial.controls.boost
            drone.ctrl.pitch = aerial.controls.pitch
            drone.ctrl.yaw = aerial.controls.yaw
            drone.ctrl.roll = aerial.controls.roll
            drone.ctrl.jump = aerial.controls.jump

        return StepResult(finished=packet.game_info.seconds_elapsed - self.start_time > self.duration)

class HackSubgroup(SubGroupChoreography):
    def __init__(self, game_interface: GameInterface, game_info: GameInfo, drones: List[Drone],
                 start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.renderer = self.game_interface.renderer
        self.game_info = game_info
        self.aerials: List[Aerial] = []
        self.target_list = []
        self.prev_targets = []
        self.center_of_rotation = np.array([0, 0, 0])
        self.translate_to = np.array([0, 0, 900])


    def generate_sequence(self, drones: List[Drone]):
        self.aerials = []

        if len(drones) == 0:
            return


        axis_1 = 4
        axis_2 = 4

        self.target_list = [
            np.array([
                (i % axis_1) * 200 - 300,
                ((i // axis_1) % axis_2) * 200 - 300,
                (i // (axis_1 * axis_2)) * 200 - 200
            ])
            for i in range(len(drones))
        ]

        self.prev_targets = [np.array([0, 0, 0]) for i in range(len(self.target_list))]

        for i in range(600):
            self.sequence.append(DroneListStep(self.arrange_in_grid))

        for i in range(8):
            self.sequence.append(DroneListStep(self.flight_pattern))
            self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 0.3))
            self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 0.05))
        # self.sequence.append(DroneListStep(self.flight_pattern))
        # self.sequence.append(AerialToLocation(self.game_info, Vec3(0, 4000, 1600), 5))
        # self.sequence.append(DroneListStep(self.flight_pattern))
        # self.sequence.append(AerialToLocation(self.game_info, Vec3(0, -4000, 1600), 5))

    def get_inward_rotation(self, index) -> Rotator:
        loc = self.target_list[index]
        orientation = look_at_orientation(Vec3(loc), Vec3(0, 0, 1))
        return  orientation.to_rotator()

    def get_vel_rotation(self, vel: np.array, up: Vec3) -> Rotator:
        if norm(vel) == 0 or up.is_zero():
            return Rotator(0, 0, 0)
        orientation = look_at_orientation(Vec3(vel), up)
        return orientation.to_rotator()

    def arrange_in_grid(self, packet, drones, start_time) -> StepResult:
        if len(drones) == 0 or len(self.target_list) < len(drones):
            return StepResult(finished=True)

        car_states = {}

        for index, drone in enumerate(drones):
            loc = self.target_list[index] + self.translate_to
            rotation = self.get_inward_rotation(index)

            car_states[drone.index] = CarState(
                Physics(location=Vector3(loc[0], loc[1], loc[2]),
                        velocity=Vector3(0, 0, 400),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=rotation))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def flight_pattern(self, packet, drones: List[Drone], start_time) -> StepResult:

        elapsed = packet.game_info.seconds_elapsed - start_time

        rot_vec = np.array([0, elapsed * 4, elapsed * 1])
        rotation = Rotation.from_rotvec(rot_vec)
        car_states = {}
        final_fling = elapsed > 3

        for index, drone in enumerate(drones):
            drone.ctrl.boost = True
            spawn_loc = self.target_list[index]
            loc = rotation.as_matrix().dot(spawn_loc - self.center_of_rotation) + self.center_of_rotation
            loc += self.translate_to
            prev = self.prev_targets[index]
            motion = loc - prev
            vel = motion / 0.02

            state_rot = self.get_vel_rotation(vel, Vec3(rot_vec))
            state_velocity = Vector3(0, 0, 0)
            if final_fling:
                state_velocity = Vector3(vel[0], vel[1], vel[2])

            car_states[drone.index] = CarState(
                Physics(location=Vector3(loc[0], loc[1], loc[2]),
                        velocity=state_velocity,
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=state_rot))

            self.prev_targets[index] = loc
        self.game_interface.set_game_state(GameState(cars=car_states))

        return StepResult(finished=elapsed > 3)


class HackPatterns(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

        self.game_info = GameInfo(0, 0)
        self.renderer = self.game_interface.renderer

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        self.game_info.read_packet(packet)

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()

        if len(drones) == 0:
            return

        self.sequence.append(HideBall(self.game_interface))
        self.sequence.append(LetAllCarsSpawn(self.game_interface, self.get_num_bots()))

        self.sequence.append(SubGroupOrchestrator(group_list=[
            HackSubgroup(self.game_interface, self.game_info, drones, 0)
        ]))
