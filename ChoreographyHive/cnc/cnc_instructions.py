import math
from dataclasses import dataclass
from typing import List, Dict

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Vector3, Physics, Rotator

from choreography.drone import Drone
from util.orientation import look_at_orientation
from util.vec import Vec3
from scipy.spatial.transform import Rotation
import numpy as np


@dataclass
class StateAndControls:
    state: GameState
    controls: SimpleControllerState


@dataclass()
class ThicknessKeyframe:
    progression: float
    thickness: float


class MotionTrack:

    def __init__(self, start: Vec3, end: Vec3, speed: float):
        self.start = start
        self.end = end
        self.speed = speed
        self.to_end = (end - start)
        if self.to_end.is_zero():
            self.velocity = Vec3()
        else:
            self.velocity = self.to_end.rescale(speed)
        self.total_time = self.to_end.length() / speed


@dataclass
class Instruction:
    drone_action = None
    motion_track: MotionTrack = None
    begins_path = False
    ends_path = False


@dataclass
class InstructionResult:
    finished: bool
    car_states: Dict[int, CarState]


class BoostOn(Instruction):
    @staticmethod
    def boost_on(drone: Drone):
        drone.ctrl.boost = True

    drone_action = boost_on
    begins_path = True


class BoostOff(Instruction):
    @staticmethod
    def boost_off(drone: Drone):
        drone.ctrl.boost = False

    drone_action = boost_off
    ends_path = True


class Move(Instruction):
    def __init__(self, start: Vec3, end: Vec3, speed: float):
        self.motion_track = MotionTrack(start, end, speed)


class BotCnc:
    def __init__(self, origin: Vec3, normal: Vec3, scale: float, speed: float):
        self.origin = np.array([origin.x, origin.y, origin.z])
        self.normal = normal
        self.scale = scale
        self.speed = speed
        self.previous_position = None
        self.list: List[Instruction] = []
        self.thickness_instructions: List[List[ThicknessKeyframe]] = []
        up_vector = Vec3(0, 0, 1)
        if self.normal.x == 0 and self.normal.y == 0:
            up_vector = Vec3(0, 1, 0)
        orient_basis = look_at_orientation(Vec3(0, -1, 0), Vec3(-1, 0, 0)).to_matrix()
        self.orient_matrix = orient_basis.dot(look_at_orientation(self.normal, up_vector).to_matrix())
        self.scale_matrix = np.array([[scale, 0, 0], [0, scale, 0], [0, 0, scale]])

    def activate_nozzle(self, thickness_spec: List[ThicknessKeyframe]):
        transformed_keyframes = [ThicknessKeyframe(tk.progression, tk.thickness * self.scale)
                                 for tk in thickness_spec]
        transformed_keyframes.sort(key=lambda tk: tk.progression)
        self.thickness_instructions.append(transformed_keyframes)
        self.list.append(BoostOn())

    def deactivate_nozzle(self):
        self.list.append(BoostOff())

    def move_to_position(self, x: float, y: float):
        rotated_position = self.orient_matrix.dot(np.array([x, y, 0]))
        end_arr = self.origin + rotated_position * self.scale
        end = Vec3(end_arr)
        start = self.previous_position
        if start is None:
            start = end
        self.list.append(Move(start, end, self.speed))
        self.previous_position = end


def determine_radius_from_powerstroke(step_index, progress_within_step, data: List[ThicknessKeyframe]):
    """
    Powerstroke is a tool in the Inkscape vector editing program. It encodes thickness data
    """
    progress = step_index + progress_within_step
    if progress < data[0].progression:
        return data[0].thickness

    for i in range(0, len(data) - 1):
        a = data[i]
        b = data[i + 1]
        if a.progression < progress < b.progression:
            segment_width = b.progression - a.progression
            segment_height = b.thickness - a.thickness
            ratio = (progress - a.progression) / segment_width
            return ratio * segment_height + a.thickness

    return data[-1].thickness


class CncExtruder:
    def __init__(self, drones: List[Drone], bot_cnc: BotCnc):
        self.drones = drones
        self.step_index: int = 0
        self.step_start_time: float = None
        self.bot_cnc = bot_cnc
        self.path_index = 0
        self.distance_on_current_path_from_prior_segments = 0

    def is_finished(self):
        return self.step_index >= len(self.bot_cnc.list)

    def restart(self):
        self.step_index = 0
        self.step_start_time = None
        self.path_index = 0
        self.distance_on_current_path_from_prior_segments = 0

    def arrange_drones(self, extruder_position: Vec3, velocity: Vec3, game_time: float, radius: float) -> Dict[
        int, CarState]:
        raise NotImplementedError

    def fast_forward(self, game_time, elapsed_time):
        remaining_time = elapsed_time
        while True:
            step = self.bot_cnc.list[self.step_index]

            if step.drone_action:
                for drone in self.drones:
                    step.drone_action(drone)

            if step.begins_path:
                self.distance_on_current_path_from_prior_segments = 0

            if step.ends_path:
                self.path_index += 1

            if step.motion_track:
                if remaining_time > step.motion_track.total_time:
                    remaining_time -= step.motion_track.total_time
                else:
                    self.step_start_time = game_time - remaining_time
                    break

            self.step_index += 1
            self.step_start_time = None

        return InstructionResult(self.is_finished(), {})

    def manipulate_drones(self, game_time: float) -> InstructionResult:
        step = self.bot_cnc.list[self.step_index]
        step_finished = True
        car_states = None

        if step.drone_action:
            for drone in self.drones:
                step.drone_action(drone)

        if step.begins_path:
            self.distance_on_current_path_from_prior_segments = 0

        if step.ends_path:
            self.path_index += 1

        if step.motion_track:
            if self.step_start_time:
                elapsed = game_time - self.step_start_time
                progression = elapsed / (step.motion_track.total_time + .00001)  # Avoid division by zero
                if progression < 1:
                    # This is the normal case where we're in the middle of drawing a segment
                    loc = step.motion_track.start + step.motion_track.to_end * progression
                    vel = step.motion_track.velocity
                else:
                    # Time has progressed to the point where we should already be done with this line segment.
                    self.distance_on_current_path_from_prior_segments += step.motion_track.to_end.length()
                    if self.step_index + 1 < len(self.bot_cnc.list) and self.bot_cnc.list[
                        self.step_index + 1].motion_track:
                        # The next step is also a line segment, so continue motion onto it
                        self.step_start_time = self.step_start_time + step.motion_track.total_time
                        self.step_index += 1
                        next_step = self.bot_cnc.list[self.step_index]
                        elapsed = game_time - self.step_start_time
                        progression = elapsed / (next_step.motion_track.total_time + .00001)  # Avoid division by zero
                        loc = next_step.motion_track.start + next_step.motion_track.to_end * progression
                        vel = next_step.motion_track.velocity
                    else:
                        # The next step is not a line segment, so halt at the end of this one.
                        loc = step.motion_track.end
                        vel = Vec3()

            else:
                # This is the first time we've arrived at this line segment,
                # initialize things and start at the beginning.
                loc = step.motion_track.start
                vel = step.motion_track.velocity
                progression = 0
                elapsed = 0
                self.step_start_time = game_time

            total_distance_on_current_path = self.distance_on_current_path_from_prior_segments + step.motion_track.velocity.length() * elapsed
            radius = 0
            if len(self.bot_cnc.thickness_instructions) > self.path_index:
                thickness_data = self.bot_cnc.thickness_instructions[self.path_index]
                if len(thickness_data) > 0:
                    radius = determine_radius_from_powerstroke(self.step_index, progression, thickness_data)
            car_states = self.arrange_drones(loc, vel, game_time, radius)

            if progression < 1:
                step_finished = False

        if step_finished:
            self.step_index += 1
            self.step_start_time = None

        return InstructionResult(self.is_finished(), car_states)


class RadialExtruder(CncExtruder):

    def arrange_drones(self, extruder_position: Vec3, velocity: Vec3, game_time: float, radius: float) -> Dict[
        int, CarState]:
        car_states: Dict[int, CarState] = {}
        if len(self.drones) == 0:
            return car_states
        if len(self.drones) == 1:
            drone = self.drones[0]
            car_state = CarState(physics=Physics())
            car_state.physics.velocity = velocity.to_setter()
            car_state.physics.location = Vector3(
                extruder_position.x,
                extruder_position.y,
                extruder_position.z)
            car_state.physics.rotation = Rotator(0, 0, 0)
            car_states[drone.index] = car_state
        else:
            radian_separation = math.pi * 2 / len(self.drones)
            rotation_speed = 0.01 * self.bot_cnc.speed
            radius_bonus = 1.4  # The way the bots move in practice makes the radius look too small, so compensate.
            for i, drone in enumerate(self.drones):
                rotation_amount = i * radian_separation + game_time * rotation_speed
                y_offset = math.sin(rotation_amount) * radius * radius_bonus
                x_offset = math.cos(rotation_amount) * radius * radius_bonus
                car_state = CarState(physics=Physics())
                car_state.physics.velocity = velocity.to_setter()
                car_state.physics.location = Vector3(
                    extruder_position.x + x_offset,
                    extruder_position.y + y_offset,
                    extruder_position.z)
                car_state.physics.rotation = Rotator(math.pi / 2, rotation_amount - math.pi / 2, 0)
                car_states[drone.index] = car_state
        return car_states


class VelocityAlignedExtruder(CncExtruder):

    def arrange_drones(self, extruder_position: Vec3, velocity: Vec3, game_time: float, radius: float) -> Dict[
        int, CarState]:
        car_states: Dict[int, CarState] = {}
        if len(self.drones) == 0:
            return car_states
        if len(self.drones) == 1:
            drone = self.drones[0]
            car_state = CarState(physics=Physics())
            car_state.physics.velocity = velocity.to_setter()
            car_state.physics.location = Vector3(
                extruder_position.x,
                extruder_position.y,
                extruder_position.z)
            if not velocity.is_zero():
                car_state.physics.rotation = look_at_orientation(velocity, Vec3(0, 0, 1)).to_rotator()
            car_states[drone.index] = car_state
        else:
            radian_separation = math.pi * 2 / len(self.drones)
            rotation_speed = 0.01 * self.bot_cnc.speed
            radius_bonus = 1.4  # The way the bots move in practice makes the radius look too small, so compensate.
            left_component = velocity.cross(Vec3(0.2342, 423, 2341.1)).normalized()
            up_component = velocity.cross(left_component).normalized()
            for i, drone in enumerate(self.drones):
                rotation_amount = i * radian_separation + game_time * rotation_speed
                y_offset = math.sin(rotation_amount) * radius * radius_bonus
                x_offset = math.cos(rotation_amount) * radius * radius_bonus
                car_state = CarState(physics=Physics())
                car_state.physics.velocity = velocity.to_setter()
                loc = extruder_position + x_offset * up_component + y_offset * left_component
                car_state.physics.location = loc.to_setter()
                if not velocity.is_zero():
                    car_state.physics.rotation = look_at_orientation(velocity, Vec3(0, 0, 1)).to_rotator()
                car_states[drone.index] = car_state
        return car_states
