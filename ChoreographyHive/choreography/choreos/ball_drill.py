import math
from random import random, randint
from typing import List

from RLUtilities.GameInfo import GameInfo
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.choreos.torus import TorusSubChoreography, TORUS_RATE, arrange_in_ground_circle
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone, slow_to_pos, fast_to_pos
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
        self.sequence.append(HideBall(self.game_interface))

        if len(drones) >= self.get_num_bots():
            num_rings = 13
            torus_period = 2 * math.pi / TORUS_RATE
            torus_rings = [
                TorusSubChoreography(self.game_interface, self.game_info, -i * torus_period / num_rings,
                                     drones[i * self.drones_per_ring:(i + 1) * self.drones_per_ring], 0)
                for i in range(0, num_rings)
            ]

            drill_moment = 95

            ball_drill = BallDrillChoreography(self.game_interface, drones[39:49], drill_moment)

            group_list = [
                ball_drill,
                AimBotSubgroup(self.game_interface, drones[0:39], drill_moment + ball_drill.ball_release + 0.05),
                # BallFrenzySubgroup(drones[0:39], 85)
            ]

            group_list += torus_rings

            self.sequence.append(SubGroupOrchestrator(group_list=group_list))


class BallFrenzySubgroup(SubGroupChoreography):

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.clear()
        self.sequence.append(DroneListStep(self.curve_toward_ball))

    def curve_toward_ball(self, packet, drones, start_time) -> StepResult:
        ball_pos = Vec3(packet.game_ball.physics.location)
        for drone in drones:
            drone_pos = Vec3(drone.pos)
            to_ball = ball_pos - drone_pos
            perpendicular = to_ball.cross(Vec3(0, 0, 1)).rescale(800)
            target = ball_pos + perpendicular
            slow_to_pos(drone, [target.x, target.y, target.z])
        return StepResult(finished=False)

class AimBotBall(GroupStep):
    def __init__(self, hit_list: List[Drone], game_interface):
        self.hit_list = hit_list
        self.game_interface = game_interface
        self.remaining_targets = hit_list.copy()
        self.target_drone = None
        self.recent_touch_index = None
        self.wait_time = 0.01
        self.fling_moment = None
        self.fling_speed = 7000

    def to_drone(self, game_ball, drone: Drone) -> Vec3:
        return Vec3(drone.pos) - Vec3(game_ball.physics.location)

    def is_ball_off_target(self, ball_pos: Vec3, ball_vel: Vec3, drone: Drone) -> bool:
        drone_shadow = Vec3(drone.pos) + ball_vel.rescale(100)
        to_shadow = drone_shadow - ball_pos
        return ball_vel.ang_to(to_shadow) > .1

    def lead_target(self, game_ball, drone: Drone) -> Vec3:
        to_drone = self.to_drone(game_ball, drone)
        distance = to_drone.length()
        time = distance / self.fling_speed
        future_position = Vec3(drone.vel) * time + Vec3(drone.pos)
        return future_position - Vec3(game_ball.physics.location)

    def find_next_target(self, packet) -> Drone:
        ball = packet.game_ball
        velocity = Vec3(ball.physics.velocity)
        if velocity.is_zero():
            velocity = Vec3(0, 0, -1)
        min_deviation = 100
        next_target = None
        for drone in self.remaining_targets:
            to_drone = self.lead_target(ball, drone)
            deviation = velocity.ang_to(to_drone)
            if next_target is None or deviation < min_deviation:
                next_target = drone
                min_deviation = deviation
        return next_target

    def rand_angular_velocity_component(self):
        return randint(-50, 50)

    def fling_ball(self, ball_pos: Vec3, ball_vel: Vec3, packet: GameTickPacket, change_spin: bool):
        vel = self.lead_target(packet.game_ball, self.target_drone).rescale(self.fling_speed)
        anticipated_ball_pos = ball_pos + ball_vel * 0.01
        spin = Vector3(
            self.rand_angular_velocity_component(),
            self.rand_angular_velocity_component(),
            self.rand_angular_velocity_component())
        self.game_interface.set_game_state(GameState(ball=BallState(Physics(
            location=Vector3(anticipated_ball_pos.x, anticipated_ball_pos.y, anticipated_ball_pos.z),
            velocity=Vector3(vel.x, vel.y, vel.z), angular_velocity=spin))))

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:

        latest_touch_index = packet.game_ball.latest_touch.player_index
        elapsed = packet.game_info.seconds_elapsed
        ball_pos = Vec3(packet.game_ball.physics.location)
        ball_vel = Vec3(packet.game_ball.physics.velocity)
        if self.recent_touch_index is None or self.recent_touch_index != latest_touch_index:
            # Time to find a new target
            if self.recent_touch_index is not None:
                # Knock the target off the list.
                for drone in self.remaining_targets:
                    if drone.index == latest_touch_index:
                        self.remaining_targets.remove(drone)
                        # In the torus we'll check this and use it to stop flying.
                        drone.attributes["sniped"] = True
                        break
            self.recent_touch_index = latest_touch_index
            self.fling_moment = elapsed + self.wait_time

        if self.fling_moment is not None and self.fling_moment < elapsed:
            self.target_drone = self.find_next_target(packet)
            if self.target_drone is None:
                return StepResult(finished=True)
            self.fling_ball(ball_pos, ball_vel, packet, True)
            self.fling_moment = None

        if ball_vel.is_zero():
            ball_vel = Vec3(0, 0, -1)

        if self.fling_moment is None and self.is_ball_off_target(ball_pos, ball_vel, self.target_drone):
            # We're about to miss, correct the ball mid flight!
            self.fling_ball(ball_pos, ball_vel, packet, False)

        return StepResult(finished=False)


class AimBotSubgroup(SubGroupChoreography):
    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        pass

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.clear()
        self.sequence.append(AimBotBall(drones, self.game_interface))


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
        self.ball_release = 9
        self.radius = 300

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(HideBall(self.game_interface))
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
        radius_bonus = 1.4  # The way the bots move in practice makes the radius look too small, so compensate.
        car_pitch = -math.pi / 2
        car_roll = 0

        motion_start = 3
        if elapsed_time > motion_start:
            bonus_time = elapsed_time - motion_start
            if self.free_ball:
                bonus_time -= (elapsed_time - self.ball_release) * 5
            car_pitch = min(0, -math.pi / 2 + bonus_time * 1)
            car_roll = min(math.pi, bonus_time * 4)
            if self.free_ball:
                self.radius += 0.12
            else:
                self.radius = 300 - bonus_time * 35

        self.rotation_speed = 5 / self.radius + 0.03

        ball_height = max(4000 - elapsed_time * 500, 1870)

        self.rotation_amount += self.rotation_speed

        for i, drone in enumerate(drones):
            drone_rotation_amount = i * radian_separation + self.rotation_amount
            y_offset = math.sin(drone_rotation_amount) * self.radius * radius_bonus
            x_offset = math.cos(drone_rotation_amount) * self.radius * radius_bonus
            car_state = CarState(physics=Physics())
            car_state.physics.velocity = Vector3(0, 0, 0)  # TODO: motion toward next
            car_state.physics.location = Vector3(
                drill_position.x + x_offset,
                drill_position.y + y_offset,
                drill_position.z)
            car_state.physics.rotation = Rotator(car_pitch, drone_rotation_amount, car_roll)
            car_states[drone.index] = car_state
            drone.ctrl.boost = elapsed_time > 5

        ball_state = None

        if not self.free_ball:
            if elapsed_time < self.ball_release:
                ball_state = BallState(Physics(
                    location=Vector3(drill_position.x, drill_position.y, ball_height)))
            else:
                self.free_ball = True
                ball_state = BallState(Physics(
                    velocity=Vector3(0, 1000, -10000)))

        self.game_interface.set_game_state(GameState(cars=car_states, ball=ball_state))
        return StepResult(finished=elapsed_time > self.ball_release + 40)

