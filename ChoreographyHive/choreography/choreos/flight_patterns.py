import math
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import vec3, Aerial
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
from util.vec import Vec3

BASE_CAR_Z = 17


class SlipFlight(SubGroupChoreography):
    def __init__(self, game_interface: GameInterface, game_info: GameInfo, drones: List[Drone],
                 start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.renderer = self.game_interface.renderer
        self.game_info = game_info
        self.aerials: List[Aerial] = []
        self.target_list = []
        self.center_of_rotation = np.array([0, -3000, 800])


    def generate_sequence(self, drones: List[Drone]):
        self.aerials = []

        if len(drones) == 0:
            return


        per_row = 8
        self.target_list = [
            np.array([
                (i % per_row) * 200 - 1000,
                -4800,
                (i // per_row) * 200 + 200
            ])
            for i in range(len(drones))
        ]

        for i in range(4):
            self.sequence.append(DroneListStep(self.arrange_in_grid))

        self.sequence.append(DroneListStep(self.flight_pattern))

    def arrange_in_grid(self, packet, drones, start_time) -> StepResult:
        if len(drones) == 0 or len(self.target_list) < len(drones):
            return StepResult(finished=True)

        car_states = {}

        for index, drone in enumerate(drones):
            loc = self.target_list[index]

            car_states[drone.index] = CarState(
                Physics(location=Vector3(loc[0], loc[1], loc[2]),
                        velocity=Vector3(0, 0, 400),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(math.pi / 2, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def flight_pattern(self, packet, drones: List[Drone], start_time) -> StepResult:

        # self.renderer.begin_rendering(drones[0].index)
        radian_spacing = 2 * math.pi / len(drones)

        if len(self.aerials) == 0:
            for index, drone in enumerate(drones):
                aerial = Aerial(self.game_info.cars[drone.index], vec3(0, 0, 0), 0)
                aerial.t_arrival = start_time + 5.7
                self.aerials.append(aerial)

        elapsed = packet.game_info.seconds_elapsed - start_time
        # radius = 4000 - elapsed * 100

        # self.renderer.draw_string_2d(10, 10, 2, 2, f"r {radius}", self.renderer.white())
        # self.renderer.draw_string_2d(10, 30, 2, 2, f"z {drones[0].pos[2]}", self.renderer.white())


        rotation = Rotation.from_rotvec([0, elapsed * 0.5, 0]).as_matrix()


        for index, drone in enumerate(drones):
            aerial = self.aerials[index]
            spawn_loc = self.target_list[index]
            rotated_spawn = rotation.dot(spawn_loc - self.center_of_rotation) + self.center_of_rotation
            target = Vec3(rotated_spawn[0], 5000, rotated_spawn[2])
            # self.renderer.draw_line_3d(drone.pos, target, self.renderer.yellow())
            aerial.target = vec3(target.x, target.y, target.z)
            aerial.step(0.008)
            drone.ctrl.boost = aerial.controls.boost
            drone.ctrl.pitch = aerial.controls.pitch
            drone.ctrl.yaw = aerial.controls.yaw
            drone.ctrl.roll = aerial.controls.roll
            drone.ctrl.jump = aerial.controls.jump

        self.previous_seconds_elapsed = packet.game_info.seconds_elapsed
        # self.renderer.end_rendering()

        return StepResult(finished=elapsed > 7)


class FlightPatterns(Choreography):

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
            SlipFlight(self.game_interface, self.game_info, drones, 0)
        ]))
