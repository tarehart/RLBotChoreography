import math
from typing import List

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn
from choreography.drone import Drone
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, SubGroupChoreography, \
    SubGroupOrchestrator, GroupStep
from util.orientation import look_at_orientation
from util.vec import Vec3

BASE_CAR_Z = 17


def stagger(n):
    return (n % 2) * 2 - 1


class CruiseFormation(SubGroupChoreography):

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.game_interface = game_interface

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.pose_drones))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 3.3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, steer=-1.0, boost=True), 0.3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=-1.0, steer=1.0, boost=True), 0.2))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, steer=1.0, handbrake=True, boost=True), 0.749))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 0.5))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, steer=0.1), 0.7))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, steer=-0.1), 0.9))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(jump=True, boost=True, roll=-1.0, yaw=1.0), 1))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True, pitch=0.6, yaw=-1.0), 0.2))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 0.3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0), 0.5))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 2.5))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, roll=1), 0.6))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True, roll=-1), 0.1))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1.0, boost=True), 2))

    def pose_drones(self, packet, drones, start_time) -> StepResult:
        car_states = {}
        drones_per_wing = 7
        for index, drone in enumerate(drones):
            wing = index // drones_per_wing
            wing_index = index % drones_per_wing
            rank = 0 if wing_index == 0 else (wing_index + 1) // 2
            x_value = stagger(wing_index) * rank * 150
            y_value = rank * -150 + wing * -300 - 4000
            car_states[drone.index] = CarState(
                Physics(location=Vector3(x_value, y_value, 40),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, math.pi / 2, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

class SoccerTunnelMember(SubGroupChoreography):

    def __init__(self, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, boost=True), 1.6))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, jump=True, boost=True), .3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, boost=True), .01))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, jump=True, boost=True, pitch=-1), .3))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(throttle=1, boost=True), .3))

class LineUpSoccerTunnel(SubGroupChoreography):

    def __init__(self, drones: List[Drone], start_time: float, game_interface):
        super().__init__(drones, start_time)
        self.game_interface = game_interface

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.line_up))

    def line_up(self, packet, drones: List[Drone], start_time) -> StepResult:
        car_states = {}
        for drone in drones:
            x_value = stagger(drone.index) * 3500
            car_states[drone.index] = CarState(
                Physics(location=Vector3(x_value, drone.index * 92 - 2000, 40),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, math.pi / 2 + stagger(drone.index) * math.pi / 2, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)


class FastFly(SubGroupChoreography):

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float, location: Vec3,
                 direction: Vec3):
        super().__init__(drones, start_time)
        self.game_interface = game_interface
        self.location = location
        self.direction = direction
        self.generate_sequence(drones)

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.clear()
        self.sequence.append(DroneListStep(self.pose_drones))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 3))

    def pose_drones(self, packet, global_drones, start_time) -> StepResult:
        car_states = {}
        num_drones = len(self.drones)
        spacing = 75
        orientation = look_at_orientation(self.direction, Vec3(0, 1, 0))
        for index, drone in enumerate(self.drones):
            loc = self.location + orientation.right.rescale(index * spacing - num_drones * spacing / 2)
            car_states[drone.index] = CarState(
                Physics(location=Vector3(loc.x, loc.y, loc.z),
                        velocity=Vector3(self.direction.x, self.direction.y, self.direction.z),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=orientation.to_rotator()))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)


class GrandTourChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(LetAllCarsSpawn(self.game_interface, self.get_num_bots()))
        self.sequence.append(DroneListStep(self.position_ball))

        if len(drones) < 48:
            return

        group_list = [
            CruiseFormation(game_interface=self.game_interface, drones=drones[:12], start_time=0),
            LineUpSoccerTunnel(drones=drones[12:], start_time=0, game_interface=self.game_interface),
            FastFly(game_interface=self.game_interface, drones=[drones[12], drones[15], drones[18], drones[21]],
                    start_time=4.2, location=Vec3(-2500, 0, 200), direction=Vec3(1000, 300, 500)),
            FastFly(game_interface=self.game_interface, drones=[drones[13], drones[16], drones[19], drones[22]],
                    start_time=4.5, location=Vec3(2500, 900, 200), direction=Vec3(-1000, 300, 500)),
            FastFly(game_interface=self.game_interface, drones=[drones[14], drones[17], drones[20], drones[23]],
                    start_time=4.8, location=Vec3(-2500, 1800, 200), direction=Vec3(1000, 300, 500))
        ] + [SoccerTunnelMember([drones[i + 12]], i * .032) for i in range(36)]
        self.sequence.append(SubGroupOrchestrator(group_list=group_list))


    def position_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(3000, -2200, 118),
            velocity=Vector3(0, 0, 0.00001),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
