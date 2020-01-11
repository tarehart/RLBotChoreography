import math

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, PerDroneStep
from util.vec import Vec3


class BallDrillChoreography(Choreography):
    """
    This was used to create https://www.youtube.com/watch?v=7D5QJipyTrw
    """

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()

        pause_time = 1.5

        self.sequence.append(DroneListStep(self.hide_ball))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.drill))

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

    def drill(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line close to the ceiling.
        """
        if len(drones) == 0:
            return StepResult(finished=True)

        game_time = packet.game_info.seconds_elapsed
        elapsed_time = game_time - start_time

        drill_position = Vec3(10000, 0, 100)

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
            location=Vector3(drill_position.x, drill_position.y, drill_position.z + 400 - elapsed_time * 50)))))
        return StepResult(finished=elapsed_time > 20)


    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
