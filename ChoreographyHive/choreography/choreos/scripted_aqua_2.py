import math
from typing import List

from RLUtilities.GameInfo import GameInfo
from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.choreos.ball_drill import BallDrillChoreography, AimBotSubgroup
from choreography.choreos.fireworks import FireworkSubChoreography
from choreography.choreos.flight_patterns import SlipFlight
from choreography.choreos.grand_tour import CruiseFormation, LineUpSoccerTunnel, FastFly, SoccerTunnelMember, \
    pose_drones_in_cruise_formation
from choreography.choreos.torus import TorusSubChoreography, TORUS_RATE
from choreography.common.preparation import LetAllCarsSpawn, HideBall
from choreography.drone import Drone, slow_to_pos
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, SubGroupChoreography, \
    SubGroupOrchestrator, GroupStep, SubGroupChoreographySettable, PerDroneStep
from util.orientation import look_at_orientation
from util.vec import Vec3


class DriveSomewhere(SubGroupChoreography):
    def __init__(self, target: Vec3, drones: List[Drone], start_time: float):
        super().__init__(drones, start_time)
        self.target = target

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(PerDroneStep(self.get_drivin, 10))

    def get_drivin(self, packet, drone, start_time) -> StepResult:
        slow_to_pos(drone, [self.target.x, self.target.y, self.target.z])
        return StepResult(finished=Vec3(drone.pos).dist(self.target) < 100)

class TidyUp(SubGroupChoreographySettable):

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.tidy))

    def tidy(self, packet, drones, start_time) -> StepResult:
        car_states = {}
        for index, drone in enumerate(drones):
            car_states[drone.index] = CarState(
                Physics(location=Vector3(-4000, -4000 + drone.index * 100, 40),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)


class ScriptedAquaPart2(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.game_info = GameInfo(0, 0)

    @staticmethod
    def get_num_bots():
        return 57

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        self.game_info.read_packet(packet)

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(LetAllCarsSpawn(self.get_num_bots()))
        self.sequence.append(HideBall(-1000))

        if len(drones) < self.get_num_bots():
            return


        num_rings = 13
        torus_period = 2 * math.pi / TORUS_RATE
        drones_per_ring = 3

        slip_end_time = 14
        drill_moment = slip_end_time + 95

        ball_drill = BallDrillChoreography(self.game_interface, drones[39:49], drill_moment)

        # Aqua pt 1: mini fireworks, then drive toward big firework starting position, then launch big firework
        # Fireworks interlude using replays coleman already has
        # Aqua pt 2: Flying grid, replay starts with grid hovering, then *timed* with when last firework will go off in
        # its replay, grid starts moving about 1 second after the explosion. Proceed to torus as normal.
        # Explosion happens at about 8 seconds, so aim for flight beginning at 9 seconds

        group_list = [
            # DriveSomewhere(Vec3(1000, -4000, 0), drones[48:54], tunnel_end_time + 6),
            SlipFlight(self.game_interface, self.game_info, drones[0:48], start_time=0, arrange_time=6),
            TidyUp(self.game_interface, drones[39:], slip_end_time - 0.5)
        ] + [
            TorusSubChoreography(self.game_interface, self.game_info, -i * torus_period / num_rings + 16,
                                 drones[i * drones_per_ring:(i + 1) * drones_per_ring], slip_end_time)
            for i in range(0, num_rings)
        ] + [
            BallDrillChoreography(self.game_interface, drones[48:57], drill_moment),
            AimBotSubgroup(self.game_interface, drones[0:39], drill_moment + ball_drill.ball_release + 0.05)
        ]

        self.sequence.append(SubGroupOrchestrator(group_list=group_list))

