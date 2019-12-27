import math
from dataclasses import dataclass
from typing import List

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import vec3, Aerial
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import Drone
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


STANDARD_RADIUS = 1000

class HoverGangChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.leader_history: List[Breadcrumb] = []
        self.aerials: List[Aerial] = []
        self.angular_progress: List[float] = []
        self.game_info = GameInfo(0, 0)
        self.previous_seconds_elapsed = 0

    def generate_sequence(self, drones):
        self.sequence.clear()
        self.leader_history.clear()

        pause_time = 0.2

        self.sequence.append(DroneListStep(self.hide_ball))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.hover_in_line))

    def line_up(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """
        start_x = -2000
        y_increment = 100
        start_y = -len(drones) * y_increment / 2
        start_z = 800
        car_states = {}
        radian_spacing = 2 * math.pi / len(drones)
        radius = STANDARD_RADIUS

        for index, drone in enumerate(drones):
            progress = index * radian_spacing
            target = Vec3(radius * math.sin(progress), radius * math.cos(progress), 1000)

            car_states[drone.index] = CarState(
                Physics(location=Vector3(target.x, target.y, target.z),
                        velocity=Vector3(0, 0, 1000),
                        rotation=Rotator(math.pi / 2, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def hover_in_line(self, packet, drones: List[Drone], start_time) -> StepResult:

        self.game_info.read_packet(packet)
        radian_spacing = 2 * math.pi / len(drones)

        if len(self.aerials) == 0:
            for index, drone in enumerate(drones):
                self.aerials.append(Aerial(self.game_info.cars[index], vec3(0, 0, 0), 0))
                self.angular_progress.append(index * radian_spacing)


        elapsed = packet.game_info.seconds_elapsed - start_time
        # radius = 4000 - elapsed * 100
        time_delta = packet.game_info.seconds_elapsed - self.previous_seconds_elapsed

        for index, drone in enumerate(drones):
            radius = STANDARD_RADIUS  # TODO: vary the radius
            angular_delta = time_delta * .7  # TODO: vary this based on radius
            self.angular_progress[index] += angular_delta
            aerial = self.aerials[index]
            progress = self.angular_progress[index]
            target = Vec3(radius * math.sin(progress), radius * math.cos(progress), 1000)
            to_target = target - Vec3(drone.pos[0], drone.pos[1], drone.pos[2])
            aerial.target = vec3(target.x, target.y, target.z)
            aerial.t_arrival = drone.time + to_target.length() / 2000 + 0.3
            aerial.step(0.016)
            drone.ctrl.boost = aerial.controls.boost
            drone.ctrl.pitch = aerial.controls.pitch
            drone.ctrl.yaw = aerial.controls.yaw
            drone.ctrl.roll = aerial.controls.roll

        self.previous_seconds_elapsed = packet.game_info.seconds_elapsed

        return StepResult(finished=elapsed > 60)

    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
