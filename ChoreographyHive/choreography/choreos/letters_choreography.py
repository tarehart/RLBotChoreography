from typing import List

from rlbot.utils.game_state_util import GameState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import Drone
from choreography.group_step import DroneListStep, StepResult
from cnc.cnc_instructions import CncExtruder
from cnc.gcode_parser import GCodeParser, BotCnc
from util.vec import Vec3


class LettersChoreography(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.bot_cnc: BotCnc = None
        self.cnc_extruders: List[CncExtruder] = []

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        pass  # Allow drones to maintain their controls state.

    def generate_sequence(self, drones: List[Drone]):

        parser = GCodeParser()
        # This rlbot.nc is a G-code file created using StickFont: http://ncplot.com/stickfont/stickfont.htm
        self.bot_cnc = parser.parse_file('./cnc/rlbot.nc', Vec3(-3000, 0, 1400), Vec3(0, 0, 1), 150, 2000)

        for drone in drones:
            self.cnc_extruders.append(CncExtruder([drone], self.bot_cnc))

        self.sequence.clear()
        self.sequence.append(DroneListStep(self.run_cnc))

    def run_cnc(self, packet: GameTickPacket, drones: List[Drone], start_time) -> StepResult:
        game_time = packet.game_info.seconds_elapsed
        elapsed = game_time - start_time
        car_states = {}
        finished = True
        for i, extruder in enumerate(self.cnc_extruders):
            if i * 1 <= elapsed and not extruder.is_finished():
                instruction_result = extruder.manipulate_drones(game_time)
                if instruction_result.car_states:
                    car_states.update(instruction_result.car_states)
                finished = finished and instruction_result.finished
        if len(car_states):
            self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=finished)
