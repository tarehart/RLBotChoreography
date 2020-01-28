import math
from dataclasses import dataclass
from typing import List, Tuple

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import vec3, Aerial
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.choreos.torus import GROUND_PROCESSION_RATE
from choreography.common.preparation import LetAllCarsSpawn
from choreography.drone import Drone, slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, GroupStep, SubGroupOrchestrator, \
    SubGroupChoreography
from util.vec import Vec3

BASE_CAR_Z = 17

class ExplodeBall(GroupStep):

    def __init__(self, game_interface: GameInterface, location: Vec3):
        self.game_interface = game_interface
        self.location = location
        self.phase = 0
        self.start_time = None

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:

        if self.phase == 0:
            self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
                location=Vector3(self.location.x, self.location.y, self.location.z),
                velocity=Vector3(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)))))
            self.phase += 1
            self.start_time = packet.game_info.seconds_elapsed
            return StepResult(finished=False)
        elif self.phase == 1:
            touch_team = packet.game_ball.latest_touch.team
            enemy_polarity = touch_team * -2 + 1
            self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
                location=Vector3(0, 5300 * enemy_polarity, 100),
                velocity=Vector3(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)))))
            self.phase += 1
            return StepResult(finished=False)
        else:
            # Wait for the replay to be over.
            elapsed_time = packet.game_info.seconds_elapsed - self.start_time
            return StepResult(finished=packet.game_info.is_round_active and elapsed_time > 1)


class BigFireworkPrep(SubGroupChoreography):
    def __init__(self, drones: List[Drone], start_time: float, duration: float):
        super().__init__(drones, start_time)
        self.radius = 1200
        self.duration = duration

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.circle_for_firework))

    def circle_for_firework(self, packet, drones, start_time) -> StepResult:
        radian_spacing = 2 * math.pi / len(drones)
        elapsed = packet.game_info.seconds_elapsed - start_time

        for i, drone in enumerate(drones):
            progress = i * radian_spacing + elapsed * GROUND_PROCESSION_RATE
            target = [self.radius * math.sin(progress), self.radius * math.cos(progress), 0]
            slow_to_pos(drone, target)
            drone.ctrl.boost = False
            # drone.ctrl.throttle = min(drone.ctrl.throttle, 0.3)
        return StepResult(finished=elapsed > self.duration)

def get_big_firework_radius(num_drones: int):
    return num_drones * 100 / 6

class FireworkSubChoreography(SubGroupChoreography):

    def __init__(self, game_interface: GameInterface, game_info: GameInfo, time_offset: float, start_position: Vec3,
                 drones: List[Drone], start_time: float, use_goal_explosion=False):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.renderer = self.game_interface.renderer
        self.game_info = game_info
        self.time_offset = time_offset
        self.aerials: List[Aerial] = []
        self.previous_seconds_elapsed = 0
        self.start_position = start_position
        self.use_goal_explosion = use_goal_explosion
        self.radius = get_big_firework_radius(len(drones))

    def generate_sequence(self, drones: List[Drone]):
        self.aerials = []

        self.sequence.append(DroneListStep(self.line_up_on_ground))
        self.sequence.append(DroneListStep(self.wait_one, self.time_offset))
        for i in range(10):
            self.sequence.append(DroneListStep(self.cheater_takeoff))

        if len(drones) <= 6:
            self.sequence.append(DroneListStep(self.firework_flight))
            self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 0.8))
        else:
            self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 0.9))

        if self.use_goal_explosion:
            self.sequence.append(ExplodeBall(self.game_interface, self.start_position + Vec3(0, 0, 1800)))
        else:
            self.sequence.append(BlindBehaviorStep(SimpleControllerState(pitch=1, jump=True, boost=True), 0.05))
            self.sequence.append(BlindBehaviorStep(SimpleControllerState(pitch=-0.8, boost=True), 0.7))
            self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 0.6))

    def wait_one(self, packet, drones, start_time):
        elapsed = packet.game_info.seconds_elapsed - start_time
        return StepResult(finished=elapsed >= 1)

    def line_up_on_ground(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """

        if len(drones) == 0:
            return StepResult(finished=True)

        car_states = {}
        radian_spacing = 2 * math.pi / len(drones)

        for index, drone in enumerate(drones):
            progress = index * radian_spacing
            radial_offset = Vec3(self.radius * math.sin(progress), self.radius * math.cos(progress), 0)
            target = self.start_position + radial_offset

            car_states[drone.index] = CarState(
                Physics(location=Vector3(target.x, target.y, 50),
                        velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, progress, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def cheater_takeoff(self, packet, drones, start_time) -> StepResult:

        if len(drones) == 0:
            return StepResult(finished=True)

        car_states = {}
        per_ring = min(24, len(drones))
        radian_spacing = 2 * math.pi / len(drones)
        radius = 100 if per_ring == 6 else 650

        for index, drone in enumerate(drones):
            ring_num = index % 2
            progress = index * radian_spacing
            radial_offset = Vec3(radius * math.sin(progress), radius * math.cos(progress), 0)
            target = self.start_position + radial_offset


            car_states[drone.index] = CarState(
                Physics(location=Vector3(target.x, target.y, 100 + ring_num * 160),
                        velocity=Vector3(0, 0, 1000),
                        rotation=Rotator(math.pi / 2, 0, progress + math.pi / 2)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def firework_flight(self, packet, drones: List[Drone], start_time) -> StepResult:

        self.renderer.begin_rendering()

        if len(self.aerials) == 0:
            for index, drone in enumerate(drones):
                self.aerials.append(Aerial(self.game_info.cars[drone.index], vec3(0, 0, 0), 0))

        elapsed = packet.game_info.seconds_elapsed - start_time
        # radius = 4000 - elapsed * 100
        if self.previous_seconds_elapsed == 0:
            time_delta = 0
        else:
            time_delta = packet.game_info.seconds_elapsed - self.previous_seconds_elapsed

        for index, drone in enumerate(drones):
            # This function was fit from the following data points, where I experimentally found deltas which
            # worked well with sampled radius values.
            # {2500, 0.7}, {1000, 0.9}, {500, 1.2}, {200, 2.0}
            # Originally was 2476 / (radius + 1038)
            # angular_delta = time_delta * (800 / radius + 0.2)
            aerial = self.aerials[index]
            target = self.start_position + Vec3(0, 0, 2000)
            self.renderer.draw_line_3d(drone.pos, target, self.renderer.yellow())
            aerial.target = vec3(target.x, target.y, target.z)
            aerial.t_arrival = drone.time + 0.3
            aerial.step(time_delta)
            drone.ctrl.boost = aerial.controls.boost
            drone.ctrl.pitch = aerial.controls.pitch
            drone.ctrl.yaw = aerial.controls.yaw
            drone.ctrl.roll = aerial.controls.roll
            drone.ctrl.jump = aerial.controls.jump

        self.previous_seconds_elapsed = packet.game_info.seconds_elapsed
        self.renderer.end_rendering()

        return StepResult(finished=elapsed > 0.5)


class TapBallOnCarStep(GroupStep):

    def __init__(self, game_interface: GameInterface, car: Drone):
        self.game_interface = game_interface
        self.car = car
        self.frame_count = 0

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:
        if self.frame_count == 0:
            self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
                location=Vector3(self.car.pos[0], self.car.pos[1], self.car.pos[2] + 20),
                velocity=Vector3(0, 0, -1),
                angular_velocity=Vector3(0, 0, 0)))))
        self.frame_count += 1
        return StepResult(finished=self.frame_count > 30)


class FireworksChoreography(Choreography):

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
        pause_time = 0.2

        self.sequence.append(LetAllCarsSpawn(self.game_interface, len(drones)))
        self.sequence.append(DroneListStep(self.hide_ball))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))

        drones_per_missile = 6
        num_missiles = len(drones) // drones_per_missile
        self.sequence.append(SubGroupOrchestrator(group_list=[
            FireworkSubChoreography(self.game_interface, self.game_info, n * .5, Vec3(n * 200 - 1000, n * 1000 - 4000, 50),
                                    drones[n * drones_per_missile: (n + 1) * drones_per_missile], 0, False)
            for n in range(0, num_missiles)
        ]))

        if len(drones) >= 9:
            for i in range(0, 9):
                self.sequence.append(DroneListStep(self.line_up))
                self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 0.5))
                self.sequence.append(TapBallOnCarStep(self.game_interface, drones[i]))
                self.sequence.append(SubGroupOrchestrator(group_list=[
                    FireworkSubChoreography(self.game_interface, self.game_info, 0, Vec3(0, 0, 50), drones, 0, True)
                ]))
                self.sequence.append(LetAllCarsSpawn(self.game_interface, len(drones)))

    def line_up(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """
        start_x = -2000
        y_increment = 200
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

    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
