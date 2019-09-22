from typing import Set, List

from rlbot.utils.structures.game_data_struct import GameTickPacket

from choreography.drone import Drone


class Choreography:

    def __init__(self):
        self.sequence = []
        self.sequence_index = 0
        self.finished = False

    def step(self, packet: GameTickPacket, drones: List[Drone]):
        if self.sequence_index < len(self.sequence):
            step = self.sequence[self.sequence_index]
            result = step.perform(packet, drones)
            if result.finished:
                self.sequence_index += 1
        else:
            self.finished = True

    def generate_sequence(self):
        pass
