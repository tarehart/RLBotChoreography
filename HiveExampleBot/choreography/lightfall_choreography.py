import math

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import slow_to_pos
from choreography.group_step import BlindBehaviorStep, LambdaStep, StepResult, SynchronizedBehaviorStep


class LightfallChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

    def generate_sequence(self):
        self.sequence.clear()

        pause_time = 1.5

        self.sequence.append(LambdaStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(LambdaStep(self.line_up))
        self.sequence.append(LambdaStep(self.move_ball))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(LambdaStep(self.place_on_ceiling))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 0.1))
        self.sequence.append(SynchronizedBehaviorStep(self.drift_downward, 20))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 0.5))
        self.sequence.append(SynchronizedBehaviorStep(self.wave_jump, 10))
        self.sequence.append(LambdaStep(self.circular_procession))

    def divergent_drive(self, packet, drone, start_time) -> StepResult:
        steer = min(1, -1 + drone.index * 0.05)
        drone.ctrl = SimpleControllerState(steer=steer, throttle=1)
        return StepResult(finished=False)

    def wave_jump(self, packet, drone, start_time) -> StepResult:
        elapsed = packet.game_info.seconds_elapsed - start_time
        jump_start = drone.index * 0.1
        jump_end = jump_start + .5
        drone.ctrl = SimpleControllerState(jump=jump_start < elapsed < jump_end)
        wheel_contact = packet.game_cars[drone.index].has_wheel_contact
        return StepResult(finished=elapsed > jump_end and wheel_contact)

    def circular_procession(self, packet, drones, start_time) -> StepResult:
        radian_spacing = 2 * math.pi / len(drones)
        elapsed = packet.game_info.seconds_elapsed - start_time
        radius = 4000 - elapsed * 100
        for i, drone in enumerate(drones):
            progress = i * radian_spacing + elapsed * .5
            target = [radius * math.sin(progress), radius * math.cos(progress), 0]
            slow_to_pos(drone, target)
        return StepResult(finished=radius < 10)

    def line_up(self, packet, drones, start_time) -> StepResult:
        start_x = -2000
        start_y = -2000
        start_z = 40
        y_increment = 100
        car_states = {}
        for drone in drones:
            car_states[drone.index] = CarState(
                Physics(location=Vector3(start_x, start_y + drone.index * y_increment, start_z),
                        velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def place_on_ceiling(self, packet, drones, start_time) -> StepResult:
        start_x = 2000
        start_y = -2000
        start_z = 1900
        y_increment = 100
        car_states = {}
        for drone in drones:
            car_states[drone.index] = CarState(
                Physics(location=Vector3(start_x, start_y + drone.index * y_increment, start_z),
                        velocity=Vector3(0, 0, 0),
                        rotation=Rotator(math.pi * 1, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def drift_downward(self, packet, drone, start_time) -> StepResult:
        elapsed = packet.game_info.seconds_elapsed - start_time
        drone.ctrl = SimpleControllerState(boost=drone.vel[2] < -280, throttle=1, pitch=-0.15)
        wheel_contact = packet.game_cars[drone.index].has_wheel_contact
        return StepResult(finished=wheel_contact)

    def move_ball(self, packet, drones, start_time) -> StepResult:
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(location=Vector3(10000, 0, 0)))))
        return StepResult(finished=True)
