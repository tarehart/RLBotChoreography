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

BASE_CAR_Z = 17



class CruisePose(SubGroupChoreographySettable):

    def generate_sequence(self, drones: List[Drone]):
        self.sequence.append(DroneListStep(self.pose_drones))

    def pose_drones(self, packet, drones, start_time) -> StepResult:
        pose_drones_in_cruise_formation(drones, self.game_interface)
        return StepResult(finished=True)

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
        drones_per_wing = 7
        for index, drone in enumerate(drones):
            car_states[drone.index] = CarState(
                Physics(location=Vector3(-4000, -4000 + drone.index * 100, 40),
                        velocity=Vector3(0, 0, 0),
                        angular_velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, 0, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))
        return StepResult(finished=True)


class ScriptedAqua(Choreography):

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface
        self.game_info = GameInfo(0, 0)

    @staticmethod
    def get_num_bots():
        return 64

    def pre_step(self, packet: GameTickPacket, drones: List[Drone]):
        self.game_info.read_packet(packet)

    def generate_sequence(self, drones):
        self.sequence.clear()

        self.sequence.append(LetAllCarsSpawn(self.game_interface, self.get_num_bots()))
        self.sequence.append(HideBall(self.game_interface))

        if len(drones) < self.get_num_bots():
            return


        num_rings = 13
        torus_period = 2 * math.pi / TORUS_RATE
        drones_per_ring = 3

        pose_duration = 6
        tunnel_end_time = pose_duration + 9
        firework_end_time = tunnel_end_time + 6
        slip_end_time = firework_end_time + 6
        drones_per_missile = 6

        drill_moment = slip_end_time + 95

        ball_drill = BallDrillChoreography(self.game_interface, drones[39:49], drill_moment)

        group_list = [
            CruisePose(game_interface=self.game_interface, drones=drones[:12], start_time=0),
            CruiseFormation(game_interface=self.game_interface, drones=drones[:12], start_time=pose_duration),
            LineUpSoccerTunnel(drones=drones[12:48], start_time=pose_duration, game_interface=self.game_interface),
            FastFly(game_interface=self.game_interface, drones=[drones[12], drones[15], drones[18], drones[21]],
                    start_time=pose_duration + 4.2, location=Vec3(-2500, 0, 200), direction=Vec3(1000, 300, 500)),
            FastFly(game_interface=self.game_interface, drones=[drones[13], drones[16], drones[19], drones[22]],
                    start_time=pose_duration + 4.5, location=Vec3(2500, 900, 200), direction=Vec3(-1000, 300, 500)),
            FastFly(game_interface=self.game_interface, drones=[drones[14], drones[17], drones[20], drones[23]],
                    start_time=pose_duration + 4.8, location=Vec3(-2500, 1800, 200), direction=Vec3(1000, 300, 500))
        ] + [
            SoccerTunnelMember([drones[i + 12]], i * .032 + pose_duration) for i in range(36)
        ] + [
            FireworkSubChoreography(self.game_interface, self.game_info, n * .5, Vec3(2000, n * 1000 - 3000, 50),
                                    drones[n * drones_per_missile + 19: (n + 1) * drones_per_missile + 19], tunnel_end_time, False)
            for n in range(6)
        ] + [
            # DriveSomewhere(Vec3(1000, -4000, 0), drones[48:54], tunnel_end_time + 6),
            SlipFlight(self.game_interface, self.game_info, drones[0:48], firework_end_time),
            TidyUp(self.game_interface, drones[39:], slip_end_time)
        ] + [
            TorusSubChoreography(self.game_interface, self.game_info, -i * torus_period / num_rings + 16,
                                 drones[i * drones_per_ring:(i + 1) * drones_per_ring], slip_end_time)
            for i in range(0, num_rings)
        ] + [
            BallDrillChoreography(self.game_interface, drones[55:64], drill_moment),
            AimBotSubgroup(self.game_interface, drones[0:39], drill_moment + ball_drill.ball_release + 0.05)
        ]

        self.sequence.append(SubGroupOrchestrator(group_list=group_list))


    def position_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(3000, -2200, 118),
            velocity=Vector3(0, 0, 0.00001),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)
