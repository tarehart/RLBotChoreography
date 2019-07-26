from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator


import numpy as np
from utils import Car, a3l, a3r, a3v, orient_matrix, local, world, angle_between_vectors

class TestBot(BaseAgent):

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.agent  = Car(self.index, self.team, self.name)
        self.active = False
        self.time   = 0.0
        self.dt     = 1 / 120
        self.last_time = self.time - self.dt
        self.timer  = 0.0

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.process(packet)

        # Reset ctrl.
        ctrl = SimpleControllerState()
        ctrl.throttle = True
        ctrl.handbrake = True

        self.test()
        
        self.render()

        return ctrl

    def process(self, packet):
        # Car
        self.agent.pos      = a3v(packet.game_cars[self.agent.index].physics.location)
        self.agent.rot      = a3r(packet.game_cars[self.agent.index].physics.rotation)
        self.agent.vel      = a3v(packet.game_cars[self.agent.index].physics.velocity)
        #self.agent.ang_vel  = a3v(packet.game_cars[self.agent.index].physics.angular_velocity)
        #self.agent.dead     = packet.game_cars[self.agent.index].is_demolished
        #self.agent.wheel_c  = packet.game_cars[self.agent.index].has_wheel_contact
        #self.agent.sonic    = packet.game_cars[self.agent.index].is_super_sonic
        #self.agent.jumped   = packet.game_cars[self.agent.index].jumped
        #self.agent.d_jumped = packet.game_cars[self.agent.index].double_jumped
        #self.agent.boost    = packet.game_cars[self.agent.index].boost
        self.agent.orient_m = orient_matrix(self.agent.rot)

        # Game info
        self.active     = packet.game_info.is_round_active
        self.time       = packet.game_info.seconds_elapsed
        self.dt         = self.time - self.last_time
        self.last_time  = self.time

    def render(self):
        self.renderer.begin_rendering()
    
        car = self.agent

        front = world(car.orient_m, car.pos, a3l([1000,0,0])) - car.pos
        local_v = local(car.orient_m, a3l([0,0,0]), car.vel)
        angle2D = np.arctan2(local_v[1],local_v[0])
        angle_pure = angle_between_vectors(car.vel, front)

        self.renderer.draw_line_3d(car.pos, car.pos + front, self.renderer.white())
        self.renderer.draw_line_3d(car.pos, car.pos + car.vel, self.renderer.cyan())
        self.renderer.draw_string_2d(10, 10, 2, 2, ("angle: "+str(angle2D)), self.renderer.pink())
        self.renderer.draw_string_2d(10, 50, 2, 2, ("angle: "+str(angle_pure)), self.renderer.red())

        self.renderer.end_rendering()

    def test(self):
        if self.active:
            self.timer += self.dt

        pos     = Vector3(0,0,16.5)
        vel     = Vector3(0,0,0)
        rot     = Rotator(0,0,0)
        ang_vel = Vector3(0,0,0)
        car_state = {self.index : CarState(physics=Physics(location = pos, velocity = vel, rotation = rot, angular_velocity = ang_vel))}

        pos     = Vector3(0,0,5000)
        vel     = Vector3(0,0,0)
        rot     = Rotator(0,0,0)
        ang_vel = Vector3(0,0,0)
        ball_state = BallState(physics=Physics(location = pos, velocity = vel, rotation = rot, angular_velocity = ang_vel))

        # Uses state setting to set the game state.
        game_state = GameState(ball=ball_state, cars=car_state)
        self.set_game_state(game_state)
        self.set_game_state(game_state)
        self.set_game_state(game_state)
        self.set_game_state(game_state)
        self.set_game_state(game_state)