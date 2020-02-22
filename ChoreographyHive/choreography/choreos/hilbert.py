from typing import List

from rlbot.utils.game_state_util import GameState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone
from choreography.group_step import DroneListStep, StepResult, SubGroupChoreographySettable, SubGroupOrchestrator
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
    def __init__(self, extent: float, speed: float):
        curve_tuples = moore(4, -extent, -extent, extent * 2, 0, 0, extent * 2)
        # self.points = [Vec3(p[0], p[1], 80) for p in curve_tuples]
        self.bot_cnc = BotCnc(Vec3(0, 0, 50), Vec3(0, 0, 1), 1, speed)
        for index, point in enumerate(curve_tuples):
            self.bot_cnc.move_to_position(point[0], point[1])
            if index == 0:
                self.bot_cnc.activate_nozzle([])


class MooreCurveChoreo(Choreography):

    def __init__(self, game_interface):
        super().__init__()
        self.game_interface = game_interface

    def generate_sequence(self, drones: List[Drone]):
        if len(drones) == 0:
            return
        self.sequence.append(HideBall(-400))
        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(SubGroupOrchestrator([MooreCurveSubgroup(self.game_interface, drones, 0)]))

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        pass  # Allow drones to maintain their controls state.

    @staticmethod
    def get_num_bots():
        return 64

class MooreCurveSubgroup(SubGroupChoreographySettable):

    def __init__(self, game_interface: GameInterface, drones: List[Drone], start_time: float, speed=1300, fast_forward=0):
        super().__init__(game_interface, drones, start_time)
        self.game_interface = game_interface
        self.time_between_cars = 0.75 * (1300 / speed) * (64 / len(drones))
        self.moore_curve = MooreCurve(extent=2000, speed=speed)
        self.cnc_extruders: List[CncExtruder] = []
        self.fast_forward = fast_forward
        self.cnc_started = False

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        pass  # Allow drones to maintain their controls state.

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.clear()
        self.cnc_extruders.clear()
        for drone in drones:
            self.cnc_extruders.append(VelocityAlignedExtruder([drone], self.moore_curve.bot_cnc))
        self.sequence.append(DroneListStep(self.run_cnc))

    def run_cnc(self, packet: GameTickPacket, drones: List[Drone], start_time) -> StepResult:
        game_time = packet.game_info.seconds_elapsed
        elapsed = game_time - start_time
        car_states = {}
        finished = True

        if not self.cnc_started:
            for i, extruder in enumerate(self.cnc_extruders):
                ffwd = self.fast_forward - i * self.time_between_cars
                if ffwd > 0:
                    extruder.fast_forward(game_time, ffwd)
            self.cnc_started = True

        for i, extruder in enumerate(self.cnc_extruders):
            if extruder.is_finished():
                extruder.restart()
            if i * self.time_between_cars <= elapsed + self.fast_forward and not extruder.is_finished():
                instruction_result = extruder.manipulate_drones(game_time)
                if instruction_result.car_states:
                    car_states.update(instruction_result.car_states)
                finished = finished and instruction_result.finished
        if len(car_states):
            self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=finished)
