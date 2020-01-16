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
            num_rings = 13
            torus_period = 2 * math.pi / TORUS_RATE
            torus_rings = [
                TorusSubChoreography(self.game_interface, self.game_info, -i * torus_period / num_rings,
                                     drones[i * self.drones_per_ring:(i + 1) * self.drones_per_ring], 0)
                for i in range(0, num_rings)
            ]
            self.sequence.append(SubGroupOrchestrator(group_list=torus_rings + [BallDrillChoreography(self.game_interface, drones[39:49], 40)]))


class BallDrillChoreography(SubGroupChoreography):
    """
    This was used to create https://www.youtube.com/watch?v=7D5QJipyTrw
    """

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.rotation_amount = 0
        self.rotation_speed = 0.04
        self.free_ball = False

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

        drill_position = Vec3(0, 0, 1900)

        car_states = {}
        radian_separation = math.pi * 2 / len(drones)
        radius = 300
        radius_bonus = 1.4  # The way the bots move in practice makes the radius look too small, so compensate.
        car_pitch = -math.pi / 2
        car_roll = 0

        motion_start = 3
        ball_release = 9
        if elapsed_time > motion_start:
            bonus_time = elapsed_time - motion_start
            if self.free_ball:
                bonus_time -= (elapsed_time - ball_release) * 5
            car_pitch = min(0, -math.pi / 2 + bonus_time * 1)
            car_roll = min(math.pi, bonus_time * 4)
            if self.free_ball:
                self.rotation_speed *= 0.99
            self.rotation_speed += 0.0005
            radius -= bonus_time * 40

        ball_height = max(4000 - elapsed_time * 500, 1870)

        self.rotation_amount += self.rotation_speed

        for i, drone in enumerate(drones):
            drone_rotation_amount = i * radian_separation + self.rotation_amount
            y_offset = math.sin(drone_rotation_amount) * radius * radius_bonus
            x_offset = math.cos(drone_rotation_amount) * radius * radius_bonus
            car_state = CarState(physics=Physics())
            car_state.physics.velocity = Vector3(0, 0, 0)  # TODO: motion toward next
            car_state.physics.location = Vector3(
                drill_position.x + x_offset,
                drill_position.y + y_offset,
                drill_position.z)
            car_state.physics.rotation = Rotator(car_pitch, drone_rotation_amount, car_roll)
            car_states[drone.index] = car_state
            drone.ctrl.boost = True

        ball_state = None

        if not self.free_ball:
            if elapsed_time < ball_release:
                ball_state = BallState(Physics(
                    location=Vector3(drill_position.x, drill_position.y, ball_height)))
            else:
                self.free_ball = True
                ball_state = BallState(Physics(
                    velocity=Vector3(0, 1000, -10000)))

        self.game_interface.set_game_state(GameState(cars=car_states, ball=ball_state))
        return StepResult(finished=elapsed_time > ball_release + 3)


    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
