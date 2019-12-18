import math
from dataclasses import dataclass
from typing import List

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import slow_to_pos, fast_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, PerDroneStep
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


class FollowTheLeaderChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.leader_history: List[Breadcrumb] = []

    def generate_sequence(self, drones):
        self.sequence.clear()
        self.leader_history.clear()

        pause_time = 1.5

        self.sequence.append(DroneListStep(self.hide_ball))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.follow_the_leader))

    def line_up(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """
        start_x = -2000
        y_increment = 100
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

    def follow_the_leader(self, packet, drones, start_time) -> StepResult:
        """
        Makes all the drones follow a lead car in an interesting pattern.
        """
        lead_index = 0
        lead_car = packet.game_cars[lead_index]
        car_states = {}

        for index, drone in enumerate(drones):
            if index == lead_index:
                drone.ctrl.throttle = 1.0
                time_index = get_time_index(packet)
                last_breadcrumb = None
                if len(self.leader_history) > 0:
                    last_breadcrumb = self.leader_history[-1]
                if last_breadcrumb is None or time_index != last_breadcrumb.time_index:
                    self.leader_history.append(Breadcrumb(
                        Vec3(lead_car.physics.location),
                        Vec3(lead_car.physics.velocity),
                        time_index, 
                        lead_car.has_wheel_contact))
                    if len(self.leader_history) > len(drones):
                        self.leader_history.pop(0)
                continue

            if len(self.leader_history) <= index:
                continue

            breadcrumb = self.leader_history[-index]

            air_trail_position = None
            if not breadcrumb.has_wheel_contact:
                normvel = breadcrumb.velocity.normalized()
                right = normvel.cross(Vec3(0, 0, 1))
                up = normvel.cross(right)
                # TODO: use a periodic function to stagger the followers based on index
                # TODO: transform the stagger based on the current orientation of the bot
                air_trail_position = breadcrumb.position + right + up

            if air_trail_position is not None and air_trail_position.z >= BASE_CAR_Z:
                car_states[drone.index] = CarState(
                    Physics(location=Vector3(air_trail_position.x, air_trail_position.y, air_trail_position.z),
                            velocity=Vector3(0, 0, 0),
                            angular_velocity=Vector3(0, 0, 0),
                            rotation=Rotator(math.pi * 1, 0, 0)))
                drone.ctrl.boost = True
            else:
                target = breadcrumb.position
                slow_to_pos(drone, [target.x, target.y, target.z])

        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=False)

    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
