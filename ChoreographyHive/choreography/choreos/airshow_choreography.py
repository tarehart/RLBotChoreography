import math

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn
from choreography.drone import slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, PerDroneStep


class AirshowChoreography(Choreography):
    """
    This was used to create https://www.youtube.com/watch?v=7D5QJipyTrw
    """

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

    @staticmethod
    def get_num_bots():
        return 8

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 0.3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=0.7), 2))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, pitch=-0.12), 1.2))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(jump=True, yaw=-1, roll=1, boost=True), 0.001))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, pitch=-1), 1))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, roll=1), 0.55))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, roll=-1), 0.05))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, pitch=1), 0.3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, pitch=-1), 0.1))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, steer=1), 3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 1))

    def wave_jump(self, packet, drone, start_time) -> StepResult:
        """
        Makes all cars jump in sequence, "doing the wave" if they happen to be lined up.
        https://gfycat.com/remorsefulsillyichthyosaurs
        """
        elapsed = packet.game_info.seconds_elapsed - start_time
        jump_start = drone.index * 0.06
        jump_end = jump_start + .5
        drone.ctrl = SimpleControllerState(jump=jump_start < elapsed < jump_end)
        wheel_contact = packet.game_cars[drone.index].has_wheel_contact
        return StepResult(finished=elapsed > jump_end and wheel_contact)

    def circular_procession(self, packet, drones, start_time) -> StepResult:
        """
        Makes all cars drive in a slowly shrinking circle.
        https://gfycat.com/yearlygreathermitcrab
        """
        radian_spacing = 2 * math.pi / len(drones)
        elapsed = packet.game_info.seconds_elapsed - start_time
        radius = 4000 - elapsed * 100
        for i, drone in enumerate(drones):
            progress = i * radian_spacing + elapsed * .5
            target = [radius * math.sin(progress), radius * math.cos(progress), 0]
            slow_to_pos(drone, target)
        return StepResult(finished=radius < 10)

    def line_up(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """
        start_y = -5100
        x_increment = 170
        start_x = -len(drones) * x_increment / 2
        start_z = 1500
        car_states = {}
        for drone in drones:
            car_states[drone.index] = CarState(
                Physics(location=Vector3(start_x + drone.index * x_increment, start_y, start_z),
                        velocity=Vector3(0, 0, 500),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(math.pi / 2, math.pi / 2, math.pi)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def place_near_ceiling(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line close to the ceiling.
        """
        start_x = 2000
        y_increment = 100
        start_y = -len(drones) * y_increment / 2
        start_z = 1900
        car_states = {}
        for drone in drones:
            car_states[drone.index] = CarState(
                Physics(location=Vector3(start_x, start_y + drone.index * y_increment, start_z),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(math.pi * 1, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def drift_downward(self, packet, drone, start_time) -> StepResult:
        """
        Causes cars to boost and pitch until they land on their wheels. This is tuned to work well when
        place_near_ceiling has just been called.
        """
        drone.ctrl = SimpleControllerState(boost=drone.vel[2] < -280, throttle=1, pitch=-0.15)
        wheel_contact = packet.game_cars[drone.index].has_wheel_contact
        return StepResult(finished=wheel_contact)

    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
