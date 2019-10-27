import math
from dataclasses import dataclass
from typing import Optional, List, Dict

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Vector3, Physics, Rotator

from choreography.drone import Drone
from util.vec import Vec3


@dataclass
class StateAndControls:
    state: GameState
    controls: SimpleControllerState


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


@dataclass
class InstructionResult:
    finished: bool
    car_states: Dict[int, CarState]


class BoostOn(Instruction):
    @staticmethod
    def boost_on(drone: Drone):
        drone.ctrl.boost = True

    drone_action = boost_on


class BoostOff(Instruction):
    @staticmethod
    def boost_off(drone: Drone):
        drone.ctrl.boost = False

    drone_action = boost_off


class Move(Instruction):
    def __init__(self, start: Vec3, end: Vec3, speed: float):
        self.motion_track = MotionTrack(start, end, speed)


class BotCnc:
    def __init__(self, origin: Vec3, normal: Vec3, scale: float, speed: float):
        self.origin = origin
        self.normal = normal
        self.scale = scale
        self.speed = speed
        self.previous_position = origin
        self.list: List[Instruction] = []

    def activate_nozzle(self):
        self.list.append(BoostOn())

    def deactivate_nozzle(self):
        self.list.append(BoostOff())

    def move_to_position(self, x: float, y: float):
        end = self.origin + Vec3(x, y) * self.scale
        # TODO: incorporate self.normal by doing some kind of rotation transform.
        self.list.append(Move(self.previous_position, end, self.speed))
        self.previous_position = end


@dataclass
class CncExtruder:
    def __init__(self, drones: List[Drone], bot_cnc: BotCnc):
        self.drones = drones
        self.step_index: int = 0
        self.step_start_time: float = None
        self.bot_cnc = bot_cnc

    def is_finished(self):
        return self.step_index >= len(self.bot_cnc.list)

    def arrange_drones(self, extruder_position: Vec3, velocity: Vec3, game_time: float) -> Dict[int, CarState]:
        car_states: Dict[int, CarState] = {}
        for i, drone in enumerate(self.drones):
            x_offset = i * 100
            car_state = CarState(physics=Physics())
            car_state.physics.velocity = velocity.to_setter()
            car_state.physics.location = Vector3(
                extruder_position.x + x_offset,
                extruder_position.y,
                extruder_position.z)
            car_state.physics.rotation = Rotator(math.pi / 2, 0, 0)
            car_states[drone.index] = car_state
        return car_states

    def manipulate_drones(self, game_time: float) -> InstructionResult:
        step = self.bot_cnc.list[self.step_index]
        step_finished = True
        car_states = None

        if step.drone_action:
            for drone in self.drones:
                step.drone_action(drone)

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
                    if self.step_index + 1 < len(self.bot_cnc.list) and self.bot_cnc.list[self.step_index + 1].motion_track:
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
                self.step_start_time = game_time

            car_states = self.arrange_drones(loc, vel, game_time)

            if progression < 1:
                step_finished = False

        if step_finished:
            self.step_index += 1
            self.step_start_time = None

        return InstructionResult(self.is_finished(), car_states)
