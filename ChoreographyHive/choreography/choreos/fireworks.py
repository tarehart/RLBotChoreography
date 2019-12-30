import math
from dataclasses import dataclass
from typing import List, Tuple

from RLUtilities.GameInfo import GameInfo
from RLUtilities.Maneuvers import vec3, Aerial
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.messages.flat.GameTickPacket import GameTickPacket
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import Drone, slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, GroupStep
from util.vec import Vec3

BASE_CAR_Z = 17


class FireworkSubChoreography(Choreography):

    def __init__(self, game_interface: GameInterface, game_info: GameInfo, time_offset: float, start_position: Vec3):
        super().__init__()
        self.game_interface = game_interface
        self.renderer = self.game_interface.renderer
        self.game_info = game_info
        self.time_offset = time_offset
        self.aerials: List[Aerial] = []
        self.previous_seconds_elapsed = 0
        self.start_position = start_position

    def generate_sequence(self, drones: List[Drone]):
        self.aerials = []

        self.sequence.append(DroneListStep(self.line_up_on_ground))
        self.sequence.append(DroneListStep(self.wait_one, self.time_offset))
        self.sequence.append(DroneListStep(self.cheater_takeoff))
        self.sequence.append(DroneListStep(self.cheater_takeoff))
        self.sequence.append(DroneListStep(self.cheater_takeoff))
        self.sequence.append(DroneListStep(self.cheater_takeoff))
        self.sequence.append(DroneListStep(self.firework_flight))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 0.8))
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
        radius = 100

        for index, drone in enumerate(drones):
            progress = index * radian_spacing
            radial_offset = Vec3(radius * math.sin(progress), radius * math.cos(progress), 0)
            target = self.start_position + radial_offset

            car_states[drone.index] = CarState(
                Physics(location=Vector3(target.x, target.y, 50),
                        velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, progress, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def cheater_takeoff(self, packet, drones, start_time) -> StepResult:
        """
        Puts all the cars in a tidy line, very close together.
        """

        if len(drones) == 0:
            return StepResult(finished=True)

        car_states = {}
        radian_spacing = 2 * math.pi / len(drones)
        radius = 100

        for index, drone in enumerate(drones):
            progress = index * radian_spacing
            radial_offset = Vec3(radius * math.sin(progress), radius * math.cos(progress), 0)
            target = self.start_position + radial_offset

            car_states[drone.index] = CarState(
                Physics(location=Vector3(target.x, target.y, 100),
                        velocity=Vector3(0, 0, 1000),
                        rotation=Rotator(math.pi / 2, 0, progress + math.pi / 2)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)

    def firework_flight(self, packet, drones: List[Drone], start_time) -> StepResult:

        self.game_info.read_packet(packet)
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


class FireworkStep(GroupStep):

    def __init__(self, game_interface: GameInterface, game_info: GameInfo):
        self.sub_choreographies: List[Choreography] = []
        self.game_interface = game_interface
        self.game_info = game_info
        self.drones_per_ring = 6

    def slice_drones(self, drones: List, index):
        return drones[index * self.drones_per_ring: (index + 1) * self.drones_per_ring]

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:

        if len(drones) == 0:
            return StepResult(finished=True)

        if len(self.sub_choreographies) == 0:
            num_rings = len(drones) // self.drones_per_ring
            self.sub_choreographies = [FireworkSubChoreography(self.game_interface, self.game_info, n * .5, Vec3(n * 200 - 1000, n * 1000 - 4000, 50))
                                       for n in range(0, num_rings)]

            for index, sub_choreo in enumerate(self.sub_choreographies):
                sub_choreo.generate_sequence(self.slice_drones(drones, index))

        all_finished = True
        for index, sub_choreo in enumerate(self.sub_choreographies):
            sub_choreo.step(packet, self.slice_drones(drones, index))
            all_finished = all_finished and sub_choreo.finished

        return StepResult(finished=all_finished)

class FireworksChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

        self.game_info = GameInfo(0, 0)
        self.renderer = self.game_interface.renderer

    @staticmethod
    def get_num_bots():
        return 48

    def generate_sequence(self, drones):
        self.sequence.clear()
        pause_time = 0.2

        self.sequence.append(DroneListStep(self.hide_ball))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), pause_time))
        self.sequence.append(DroneListStep(self.line_up))
        self.sequence.append(FireworkStep(self.game_interface, self.game_info))

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

    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
