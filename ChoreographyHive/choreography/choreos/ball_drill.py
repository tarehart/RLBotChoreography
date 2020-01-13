import math
from typing import List

from RLUtilities.GameInfo import GameInfo
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.choreos.torus import TorusSubChoreography, TORUS_RATE, arrange_in_ground_circle
from choreography.common.preparation import LetAllCarsSpawn
from choreography.drone import Drone
from choreography.group_step import DroneListStep, StepResult, SubGroupChoreography, \
    SubGroupOrchestrator, GroupStep
from util.vec import Vec3


class DrillIntoTorusChoreography(Choreography):

    def __init__(self, game_interface):
        super().__init__()
        self.drones_per_ring = 3
        self.game_interface = game_interface
        self.game_info = GameInfo(0, 0)

    @staticmethod
    def get_num_bots():
        return 48

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        self.game_info.read_packet(packet)

    def generate_sequence(self, drones: List[Drone]):

        self.sequence.append(LetAllCarsSpawn(self.game_interface, self.get_num_bots()))

        if len(drones) >= self.get_num_bots():
            num_rings = 9
            torus_period = 2 * math.pi / TORUS_RATE
            torus_rings = [
                TorusSubChoreography(self.game_interface, self.game_info, -i * torus_period / num_rings,
                                     drones[i * self.drones_per_ring:(i + 1) * self.drones_per_ring], 0)
                for i in range(0, num_rings)
            ]
            self.sequence.append(SubGroupOrchestrator(group_list=torus_rings + [BallDrillChoreography(self.game_interface, drones[36:49], 15)]))


class BallDrillChoreography(SubGroupChoreography):
    """
    This was used to create https://www.youtube.com/watch?v=7D5QJipyTrw
    """

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(DroneListStep(self.hide_ball))
        self.sequence.append(DroneListStep(self.arrange_in_ground_circle))
        self.sequence.append(DroneListStep(self.drill))

    def arrange_in_ground_circle(self, packet, drones, start_time) -> StepResult:
        arrange_in_ground_circle(drones, self.game_interface, 800, 0)
        return StepResult(finished=True)

    def drill(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line close to the ceiling.
        """
        if len(drones) == 0:
            return StepResult(finished=True)

        game_time = packet.game_info.seconds_elapsed
        elapsed_time = game_time - start_time

        drill_position = Vec3(0, 0, 4000 - elapsed_time * 500)

        car_states = {}
        radian_separation = math.pi * 2 / len(drones)
        rotation_speed = 2
        radius = 300
        radius_bonus = 1.4  # The way the bots move in practice makes the radius look too small, so compensate.
        for i, drone in enumerate(drones):
            rotation_amount = i * radian_separation + game_time * rotation_speed
            y_offset = math.sin(rotation_amount) * radius * radius_bonus
            x_offset = math.cos(rotation_amount) * radius * radius_bonus
            car_state = CarState(physics=Physics())
            car_state.physics.velocity = Vector3(0, 0, 0)  # TODO: motion toward next
            car_state.physics.location = Vector3(
                drill_position.x + x_offset,
                drill_position.y + y_offset,
                drill_position.z)
            car_state.physics.rotation = Rotator(math.pi / 2, rotation_amount - math.pi / 2, 0)
            car_states[drone.index] = car_state
            drone.ctrl.boost = True

        self.game_interface.set_game_state(GameState(cars=car_states, ball=BallState(Physics(
            location=Vector3(drill_position.x, drill_position.y, drill_position.z + 100)))))
        return StepResult(finished=elapsed_time > 5)


    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
