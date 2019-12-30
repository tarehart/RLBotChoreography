import math
from dataclasses import dataclass
from typing import List, Tuple

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import vec3, Aerial
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import Drone, slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult
from util.vec import Vec3

BASE_CAR_Z = 17

@dataclass
class Breadcrumb:
    position: Vec3
    velocity: Vec3
    time_index: int
    has_wheel_contact: bool


def get_time_index(packet):
    seconds_elapsed = packet.game_info.seconds_elapsed
    return int(seconds_elapsed * 4)  # Every quarter second


def stagger(n):
    return (n % 2) * 2 - 1


class Piecewise:
    def __init__(self, points: List[Tuple[float, float]]):
        self.points = points

    def lerp(self, x: float):
        if self.points[0][0] > x:
            return self.points[0][1]
        if self.points[-1][0] < x:
            return self.points[-1][1]

        for i in range(0, len(self.points) - 1):
            a = self.points[i]
            b = self.points[i + 1]
            if x > b[0]:
                continue
            span = b[0] - a[0]
            to_x = x - a[0]
            progress = to_x / span
            vertical_span = b[1] - a[1]
            return a[1] + vertical_span * progress


STANDARD_RADIUS = 4000
RADIUS_SPEED = Piecewise([(200, 2.0), (500, 1.2), (1400, 0.7), (2500, 0.5), (4000, 0.5)])

class HoverGangChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.leader_history: List[Breadcrumb] = []
        self.aerials: List[Aerial] = []
        self.angular_progress: List[float] = []
        self.game_info = GameInfo(0, 0)
        self.previous_seconds_elapsed = 0
        self.renderer = self.game_interface.renderer

    def generate_sequence(self, drones):
        self.sequence.clear()
        self.leader_history.clear()
        self.aerials = []
        self.angular_progress = []

        pause_time = 0.2

        self.sequence.append(DroneListStep(self.hide_ball))
        self.sequence.append(DroneListStep(self.line_up_on_ground))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.circular_procession))
        self.sequence.append(DroneListStep(self.torus_flight_pattern))

    def line_up(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """
        car_states = {}
        radian_spacing = 2 * math.pi / len(drones)
        radius = 4000

        for index, drone in enumerate(drones):
            progress = index * radian_spacing
            target = Vec3(radius * math.sin(progress), radius * math.cos(progress), 1000)

            car_states[drone.index] = CarState(
                Physics(location=Vector3(target.x, target.y, target.z - 500),
                        velocity=Vector3(0, 0, 800),
                        rotation=Rotator(math.pi / 2, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def line_up_on_ground(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """
        car_states = {}
        radian_spacing = 2 * math.pi / len(drones)
        radius = 4000

        for index, drone in enumerate(drones):
            progress = index * radian_spacing
            target = Vec3(radius * math.sin(progress), radius * math.cos(progress), 1000)

            car_states[drone.index] = CarState(
                Physics(location=Vector3(target.x, target.y, 800),
                        velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def circular_procession(self, packet, drones, start_time) -> StepResult:
        """
        Makes all cars drive in a slowly shrinking circle.
        https://gfycat.com/yearlygreathermitcrab
        """
        radian_spacing = 2 * math.pi / len(drones)
        elapsed = packet.game_info.seconds_elapsed - start_time
        radius = 4000 - elapsed * 100
        progress_scalar = 0.5
        for i, drone in enumerate(drones):
            progress = i * radian_spacing + elapsed * progress_scalar
            target = [radius * math.sin(progress), radius * math.cos(progress), 0]
            slow_to_pos(drone, target)
        return StepResult(finished=elapsed * progress_scalar > 2 * math.pi)

    def torus_flight_pattern(self, packet, drones: List[Drone], start_time) -> StepResult:

        self.game_info.read_packet(packet)
        self.renderer.begin_rendering()
        radian_spacing = 2 * math.pi / len(drones)

        if len(self.aerials) == 0:
            for index, drone in enumerate(drones):
                self.aerials.append(Aerial(self.game_info.cars[index], vec3(0, 0, 0), 0))
                self.angular_progress.append(index * radian_spacing)


        elapsed = packet.game_info.seconds_elapsed - start_time
        # radius = 4000 - elapsed * 100
        if self.previous_seconds_elapsed == 0:
            time_delta = 0
        else:
            time_delta = packet.game_info.seconds_elapsed - self.previous_seconds_elapsed

        torus_rate = 0.1
        radius = 1000 * (1 + math.cos(elapsed * torus_rate)) + 300
        height = 500 * (1 + math.sin(elapsed * torus_rate)) + 400

        self.renderer.draw_string_2d(10, 10, 2, 2, f"r {radius}", self.renderer.white())
        self.renderer.draw_string_2d(10, 30, 2, 2, f"z {drones[0].pos[2]}", self.renderer.white())

        for index, drone in enumerate(drones):
            # This function was fit from the following data points, where I experimentally found deltas which
            # worked well with sampled radius values.
            # {2500, 0.7}, {1000, 0.9}, {500, 1.2}, {200, 2.0}
            # Originally was 2476 / (radius + 1038)
            # angular_delta = time_delta * (800 / radius + 0.2)
            angular_delta = time_delta * RADIUS_SPEED.lerp(radius)
            self.angular_progress[index] += angular_delta
            aerial = self.aerials[index]
            progress = self.angular_progress[index]
            target = Vec3(radius * math.sin(progress), radius * math.cos(progress), height)
            to_target = target - Vec3(drone.pos[0], drone.pos[1], drone.pos[2])
            self.renderer.draw_line_3d(drone.pos, target, self.renderer.yellow())
            aerial.target = vec3(target.x, target.y, target.z)
            aerial.t_arrival = drone.time + to_target.length() / 2000 + 0.3
            aerial.step(time_delta)
            drone.ctrl.boost = aerial.controls.boost
            drone.ctrl.pitch = aerial.controls.pitch
            drone.ctrl.yaw = aerial.controls.yaw
            drone.ctrl.roll = aerial.controls.roll
            drone.ctrl.jump = aerial.controls.jump

        self.previous_seconds_elapsed = packet.game_info.seconds_elapsed
        self.renderer.end_rendering()

        return StepResult(finished=elapsed > 160)

    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
