from typing import List

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Vector3, Rotator, Physics
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn
from choreography.drone import Drone
from choreography.group_step import DroneListStep, StepResult, GroupStep, BlindBehaviorStep
from cnc.cnc_instructions import CncExtruder, RadialExtruder
from cnc.gcode_parser import GCodeParser, BotCnc
from hivemind import Hivemind
from util.orientation import Orientation, look_at_orientation
from util.vec import Vec3


def get_pyramid_height(num_bricks: int) -> int:
    height = 0
    remaining_bricks = num_bricks
    while remaining_bricks > 0:
        height += 1
        remaining_bricks -= height
    return height


class PyramidStacker(GroupStep):
    horizontal_gap = 75
    vertical_gap = 55

    def __init__(self, position: Vec3, orientation: Orientation):
        self.position = position
        self.orientation = orientation

    def perform(self, packet: GameTickPacket, drones: List[Drone]) -> StepResult:
        car_states = {}

        height = get_pyramid_height(len(drones))
        row_size = height
        row_index = 0
        layer_index = 0

        for drone in reversed(drones):

            rightward = self.orientation.right * (row_index - row_size / 2) * PyramidStacker.horizontal_gap
            upward = self.orientation.up * layer_index * PyramidStacker.vertical_gap
            position = self.position + rightward + upward

            car_states[drone.index] = CarState(
                Physics(location=position.to_setter(),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, 0, 0)))

            row_index += 1
            if row_index == row_size:
                row_index = 0
                row_size -= 1
                layer_index += 1

        Hivemind.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)


class LettersChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.bot_cnc: BotCnc = None
        self.cnc_extruders: List[CncExtruder] = []
        self.pre_cnc_bot_positions: List[Vec3] = []

    @staticmethod
    def get_num_bots():
        return 21

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        pass  # Allow drones to maintain their controls state.

    def generate_sequence(self, drones: List[Drone]):

        parser = GCodeParser()
        # This rlbot.nc is a G-code file created using StickFont: http://ncplot.com/stickfont/stickfont.htm
        self.bot_cnc = parser.parse_file('./cnc/igl.nc', Vec3(-3000, 1000, 500), Vec3(1, 0, 0), 150, 1200)

        self.cnc_extruders = [RadialExtruder([drone], self.bot_cnc) for drone in drones]

        self.sequence.clear()
        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(PyramidStacker(Vec3(-3000, 1500, 50), look_at_orientation(Vec3(1, 0, 0), Vec3(0, 0, 1))))
        self.sequence.append(BlindBehaviorStep(SimpleControllerState(), 5))
        # self.sequence.append(BlindBehaviorStep(SimpleControllerState(boost=True), 3))
        self.sequence.append(DroneListStep(self.run_cnc))

    def run_cnc(self, packet: GameTickPacket, drones: List[Drone], start_time) -> StepResult:
        if len(self.pre_cnc_bot_positions) == 0:
            self.pre_cnc_bot_positions = {drone.index: Vec3(drone.pos) for drone in drones}

        transition_time = 1
        game_time = packet.game_info.seconds_elapsed
        elapsed = game_time - start_time
        car_states = {}
        finished = True
        for i, extruder in enumerate(self.cnc_extruders):
            transition_start = i * 1
            cnc_start = transition_start + transition_time
            if cnc_start <= elapsed:
                if not extruder.is_finished():
                    instruction_result = extruder.manipulate_drones(game_time)
                    if instruction_result.car_states:
                        car_states.update(instruction_result.car_states)
                    finished = finished and instruction_result.finished
            elif transition_start <= elapsed:
                finished = False
                target = extruder.peek_position()
                if target is not None:
                    for drone in extruder.drones:
                        original_pos = self.pre_cnc_bot_positions[drone.index]
                        to_target = target - original_pos
                        progress = (elapsed - transition_start) / transition_time
                        pos = original_pos + to_target * progress
                        car_states[drone.index] = CarState(Physics(location=pos.to_setter()))
        if len(car_states):
            self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=finished)
