import math
from typing import List

from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.choreos.torus import arrange_in_ground_circle
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone
from choreography.group_step import DroneListStep, StepResult, SubGroupChoreography, \
    SubGroupOrchestrator
from util.orientation import look_at_orientation, Orientation
from util.vec import Vec3


class CircleStencil(Choreography):

    def __init__(self, game_interface):
        super().__init__()
        self.game_interface = game_interface

    @staticmethod
    def get_num_bots():
        return 3

    def generate_sequence(self, drones: List[Drone]):

        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(HideBall())

        if len(drones) >= self.get_num_bots():

            ball_drill = CircleStencilSub(self.game_interface, drones, 0, Vec3(0, 0, 1000), look_at_orientation(Vec3(1, 0, 0), Vec3(0, 0, 1)))

            group_list = [
                ball_drill
            ]

            self.sequence.append(SubGroupOrchestrator(group_list=group_list))


class CircleStencilSub(SubGroupChoreography):

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float, position: Vec3, orientation: Orientation):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.position = position
        self.orientation = orientation
        self.rotation_amount = 0
        self.rotation_speed = 0.07
        self.radius = 300

    def generate_sequence(self, drones):
        self.sequence.clear()
        self.sequence.append(DroneListStep(self.spin))

    def arrange_in_ground_circle(self, packet, drones, start_time) -> StepResult:
        arrange_in_ground_circle(drones, self.game_interface, 800, 0)
        return StepResult(finished=True)

    def spin(self, packet, drones, start_time) -> StepResult:

        if len(drones) == 0:
            return StepResult(finished=True)

        game_time = packet.game_info.seconds_elapsed
        elapsed_time = game_time - start_time

        car_states = {}
        radian_separation = math.pi * 2 / len(drones)

        self.rotation_amount += self.rotation_speed

        for i, drone in enumerate(drones):
            drone_rotation_amount = i * radian_separation + self.rotation_amount
            y_offset = math.sin(drone_rotation_amount) * self.radius * self.orientation.up
            x_offset = math.cos(drone_rotation_amount) * self.radius * self.orientation.right
            car_state = CarState(physics=Physics())
            car_state.physics.velocity = Vector3(0, 0, 0)
            car_state.physics.location = (self.position + y_offset + x_offset).to_setter()
            car_state.physics.rotation = self.orientation.to_rotator()
            car_state.physics.angular_velocity = Vector3(0, 0, 0)
            car_states[drone.index] = car_state
            drone.ctrl.boost = elapsed_time > 5

        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=elapsed_time > 20)

