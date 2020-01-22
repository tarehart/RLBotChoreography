from typing import List

from rlbot.utils.game_state_util import GameState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone
from choreography.group_step import DroneListStep, StepResult
from cnc.cnc_instructions import BotCnc, CncExtruder, VelocityAlignedExtruder
from util.vec import Vec3


def hilbert(n, x0, y0, xi, xj, yi, yj):
    """Generate a Hilbert curve.
    Taken from https://github.com/knz/spacefill/blob/master/python/spacefill.py
    This function returns a generator that yields the (x,y) coordinates
    of the Hilbert curve points from 0 to 4^n-1.
    Arguments:
    n      -- the base-4 logarithm of the number of points (ie. the function generates 4^n points).
    x0, y0 -- offset to add to all generated point coordinates.
    xi, yi -- projection-plane coordinates of the curve's I vector (i.e. horizontal, "X" axis).
    xj, yj -- projection-plane coordinates of the curve's J vector (i.e. vertical, "Y" axis).
    """
    if n <= 0:
        yield (x0 + (xi + yi) / 2, y0 + (xj + yj) / 2)
    else:
        yield from hilbert(n - 1, x0,               y0,               yi/2, yj/2, xi/2, xj/2)
        yield from hilbert(n - 1, x0 + xi/2,        y0 + xj/2,        xi/2, xj/2, yi/2, yj/2)
        yield from hilbert(n - 1, x0 + xi/2 + yi/2, y0 + xj/2 + yj/2, xi/2, xj/2, yi/2, yj/2)
        yield from hilbert(n - 1, x0 + xi/2 + yi,   y0 + xj/2 + yj,  -yi/2,-yj/2,-xi/2,-xj/2)

def moore(n, x0, y0, xi, xj, yi, yj):
    """Generate a Moore curve.
    Taken from https://github.com/knz/spacefill/blob/master/python/spacefill.py
    This function returns a generator that yields the (x,y) coordinates
    of the Moore curve points from 0 to 4^n-1.
    Arguments:
    n      -- the base-4 logarithm of the number of points (ie. the function generates 4^n points).
    x0, y0 -- offset to add to all generated point coordinates.
    xi, yi -- projection-plane coordinates of the curve's I vector (i.e. horizontal, "X" axis).
    xj, yj -- projection-plane coordinates of the curve's J vector (i.e. vertical, "Y" axis).
    """
    if n <= 0:
        yield (x0 + (xi + yi) / 2, y0 + (xj + yj) / 2)
    else:
        yield from hilbert(n - 1, x0 + xi/2        , y0 + xj/2        , -xi/2, xj/2, yi/2, yj/2)
        yield from hilbert(n - 1, x0 + xi/2 + yi/2 , y0 + xj/2  + yj/2, -xi/2, xj/2, yi/2, yj/2)
        yield from hilbert(n - 1, x0 + xi/2 + yi   , y0 + xj/2  + yj  ,  xi/2, xj/2, yi/2,-yj/2)
        yield from hilbert(n - 1, x0 + xi/2 + yi/2 , y0 + xj/2  + yj/2,  xi/2, xj/2, yi/2,-yj/2)


class MooreCurve:
    def __init__(self):
        curve_tuples = moore(4, -3000, -3000, 6000, 0, 0, 6000)
        # self.points = [Vec3(p[0], p[1], 80) for p in curve_tuples]
        self.bot_cnc = BotCnc(Vec3(0, 0, 70), Vec3(0, 0, 1), 1, 2000)
        for index, point in enumerate(curve_tuples):
            self.bot_cnc.move_to_position(point[0], point[1])
            if index == 0:
                self.bot_cnc.activate_nozzle([])


class MooreCurveChoreo(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.moore_curve = MooreCurve()
        self.cnc_extruders: List[CncExtruder] = []

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        pass  # Allow drones to maintain their controls state.

    @staticmethod
    def get_num_bots():
        return 64

    def generate_sequence(self, drones: List[Drone]):

        for drone in drones:
            self.cnc_extruders.append(VelocityAlignedExtruder([drone], self.moore_curve.bot_cnc))

        self.sequence.clear()
        self.sequence.append(HideBall(self.game_interface))
        self.sequence.append(LetAllCarsSpawn(self.game_interface, self.get_num_bots()))
        self.sequence.append(DroneListStep(self.run_cnc))

    def run_cnc(self, packet: GameTickPacket, drones: List[Drone], start_time) -> StepResult:
        game_time = packet.game_info.seconds_elapsed
        elapsed = game_time - start_time
        car_states = {}
        finished = True
        for i, extruder in enumerate(self.cnc_extruders):
            if extruder.is_finished():
                extruder.restart()
            if i * 0.7 <= elapsed and not extruder.is_finished():
                instruction_result = extruder.manipulate_drones(game_time)
                if instruction_result.car_states:
                    car_states.update(instruction_result.car_states)
                finished = finished and instruction_result.finished
        if len(car_states):
            self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=finished)
