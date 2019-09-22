from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.group_step import BlindBehaviorStep, LambdaStep, StepResult, SynchronizedBehaviorStep


class LightfallChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

    def generate_sequence(self):
        self.sequence.clear()

        pause_time = 1.5

        self.sequence.append(LambdaStep(self.init_positions))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(LambdaStep(self.init_positions))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(LambdaStep(self.init_positions))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(SynchronizedBehaviorStep(self.wave_jump, 10))
        self.sequence.append(SynchronizedBehaviorStep(self.wave_jump, 10))

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

    def init_positions(self, packet, drones) -> StepResult:
        start_x = -500
        start_y = -500
        start_z = 50
        y_increment = 100
        car_states = {}
        for drone in drones:
            car_states[drone.index] = CarState(
                Physics(location=Vector3(start_x, start_y + drone.index * y_increment, start_z),
                        rotation=Rotator(0, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)
