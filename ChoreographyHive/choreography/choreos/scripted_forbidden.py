from typing import List

from RLUtilities.GameInfo import GameInfo
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.choreos.hack_patterns import HackSubgroup
from choreography.choreos.hilbert import MooreCurveSubgroup
from choreography.choreos.scripted_aqua import TidyUp
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone
from choreography.group_step import SubGroupOrchestrator


class ScriptedForbidden(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.game_info = GameInfo(0, 0)

    @staticmethod
    def get_num_bots():
        return 48

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        self.game_info.read_packet(packet)

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(HideBall(self.game_interface))

        if len(drones) < self.get_num_bots():
            return

        self.sequence.append(SubGroupOrchestrator([MooreCurveSubgroup(self.game_interface, drones, 0, speed=600, fast_forward=100)], max_duration=4))
        self.sequence.append(SubGroupOrchestrator([HackSubgroup(self.game_interface, drones[:48], 0, arrange_time_limit=2)]))
