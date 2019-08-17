from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator

import numpy as np
from utils import Car, a3l, a3r, a3v, orient_matrix, local, world, angle_between_vectors

class TestBot(BaseAgent):

    def initialize_agent(self):
        """This runs once before the bot starts up. Initialises attributes."""
        self.agent  = Car(self.index, self.team, self.name)

        # Game info.
        self.active = False
        self.time   = 0.0
        self.dt     = 1 / 120
        self.last_time = self.time - self.dt

        # Test related.
        self.timer  = 0.0
        self.count  = 0
        self.times = []
        self.distance = []


    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """Runs every tick. Returns the bot controller.
        
        Arguments:
            packet {GameTickPacket} -- The information packet from the game.
        
        Returns:
            SimpleControllerState -- The controller for the bot.
        """
        # Run some light preprocessing.
        self.process(packet)

        # Reset ctrl.
        self.ctrl = SimpleControllerState()

        # Set the controller for the test.
        self.ctrl.throttle = True
        #self.ctrl.handbrake = True
        self.ctrl.boost = True

        # Run tests.
        #self.drift_test()
        self.dis_time_test()

        # Render information.
        #self.drift_render()

        return self.ctrl


    def process(self, packet: GameTickPacket):
        """Simplified preprocessing which just takes care of the car and game info that I need.
        
        Arguments:
            packet {GameTickPacket} -- The information packet from the game.
        """
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


    def drift_test(self):
        """Runs the drift tests."""
        self.tests = 500            # Number of tests.
        yaw = np.pi / self.tests    # Change in yaw.
        test_vel = 1400             # Starting velocity.

        if self.active:
            # Sets ball position out of bounds so it doesn't interfere.
            pos     = Vector3(0, 0, 2200)
            ball_state = BallState(physics=Physics(location = pos))

            # If the number of completed tests is less or equal to the number of tests, run tests.
            if self.count <= self.tests:
                # Save the previous test and restart timer.
                if self.timer > 5.0:
                    # Converting data to numpy array.
                    data = np.array([self.position,self.velocity,self.rotation])
                    # Saving data to file. I used absolute location because I was lazy.
                    np.save(f'D:/RLBot/ViliamVadocz/TestBot/data/test_{self.count:03}.npy', data)

                    self.timer = 0.0
                    self.count += 1

                # Setup next test.
                if self.timer == 0.0:
                    # Sets the car's physics for the next test.
                    pos     = Vector3(2500, -2300, 17.01)
                    vel     = Vector3(0, test_vel, 0)
                    rot     = Rotator(None, np.pi/2 + yaw*self.count, 0)
                    ang_vel = Vector3(0, 0, 0) 
                    car_state = {self.index : CarState(physics=Physics(location = pos, velocity = vel, rotation = rot, angular_velocity = ang_vel))}

                    # Initialises data lists. (Not using numpy arrays here because I'd have to guess the approximate size)
                    self.position = []
                    self.velocity = []
                    self.rotation = []

                # Starts collecting data. (comparing to 0.1 here instead of just using else, juse to make sure that the test has restarted.)
                elif self.timer > 0.05:
                    car_state = {self.index: CarState()}

                    self.position.append(self.agent.pos)
                    self.velocity.append(self.agent.vel)
                    self.rotation.append(self.agent.rot)

            else:
                # End of testing.
                self.ctrl.throttle = False
                self.ctrl.handbrake = False
                car_state = {self.index: CarState()}

            # Increments timer.
            self.timer += self.dt

            # Sets game state.
            game_state = GameState(ball=ball_state, cars=car_state)
            # I set it multiple times because apparently if you just do it once
            # it sometimes doesn't work and it doesn't hurt to set it more than once.
            self.set_game_state(game_state)
            self.set_game_state(game_state)
            self.set_game_state(game_state)
            self.set_game_state(game_state)
            self.set_game_state(game_state)


    def drift_render(self):
        """Renders information on the screen."""
        self.renderer.begin_rendering()
    
        car = self.agent

        # Calculates a vector from the car to the position 1000 uu in the front direction of the car.
        front = world(car.orient_m, car.pos, a3l([1000,0,0])) - car.pos
        # Calculated the velocity vector in local coordinates.
        local_v = local(car.orient_m, a3l([0,0,0]), car.vel)
        # Uses two methods to calculate angle. (The were just for testing which produces better results.)
        angle2D = np.arctan2(local_v[1],local_v[0])
        angle_pure = angle_between_vectors(car.vel, front)

        # Rendering front vector and velocity vector.
        self.renderer.draw_line_3d(car.pos, car.pos + front, self.renderer.yellow())
        self.renderer.draw_line_3d(car.pos, car.pos + car.vel, self.renderer.cyan())
        # Rendering angles.
        self.renderer.draw_string_2d(10, 10, 2, 2, "angle 2D: {}".format(angle2D), self.renderer.pink())
        self.renderer.draw_string_2d(10, 50, 2, 2, "angle 3D: {}".format(angle_pure), self.renderer.pink())
        # Rendering position and velocity.
        self.renderer.draw_string_2d(10, 110, 2, 2, "pos: {}".format(car.pos), self.renderer.cyan())
        self.renderer.draw_string_2d(10, 150, 2, 2, "vel: {}".format(car.vel), self.renderer.cyan())
        # Rendering test related stuff.
        self.renderer.draw_string_2d(10, 210, 2, 2, "test: {}/{}".format(self.count, self.tests), self.renderer.white())
        self.renderer.draw_string_2d(10, 250, 2, 2, "timer: {}".format(self.timer), self.renderer.white())

        self.renderer.end_rendering()


    def dis_time_test(self):
        """Runs the distance-time test."""
        self.tests = 10

        if self.active:
            # Sets ball position out of bounds so it doesn't interfere.
            pos     = Vector3(0, 0, 2200)
            ball_state = BallState(physics=Physics(location = pos))

            # If the number of completed tests is less or equal to the number of tests, run tests.
            if self.count <= self.tests:
                # Save the previous test and restart timer.
                if np.linalg.norm(self.agent.vel) >= 2250:
                    # Converting data to numpy array.
                    data = np.array([self.times, self.distance])
                    # Saving data to file. I used absolute location because I was lazy.
                    np.save(f'D:/RLBot/ViliamVadocz/TestBot/data/test_{self.count:02}.npy', data)

                    self.timer = 0.0
                    self.count += 1

                # Setup next test.
                if self.timer == 0.0:
                    # Sets the car's physics for the next test.
                    pos     = Vector3(0, 0, 17.01)
                    vel     = Vector3(0, 0, 0)
                    rot     = Rotator(None, np.pi/2, 0)
                    ang_vel = Vector3(0, 0, 0) 
                    car_state = {self.index : CarState(physics=Physics(location = pos, velocity = vel, rotation = rot, angular_velocity = ang_vel))}

                    # Initialises data lists. (Not using numpy arrays here because I'd have to guess the approximate size)
                    self.times = []
                    self.distance = []

                # Starts collecting data. (comparing to 0.1 here instead of just using else, juse to make sure that the test has restarted.)
                elif self.timer > 0.1:
                    car_state = {self.index: CarState()}

                    self.times.append(self.timer)
                    self.distance.append(self.agent.pos[1])

            else:
                # End of testing.
                self.ctrl.throttle = False
                self.ctrl.handbrake = False
                car_state = {self.index: CarState()}


        # Increments timer.
        self.timer += self.dt

        # Sets game state.
        game_state = GameState(ball=ball_state, cars=car_state)
        # I set it multiple times because apparently if you just do it once
        # it sometimes doesn't work and it doesn't hurt to set it more than once.
        self.set_game_state(game_state)
        self.set_game_state(game_state)
        self.set_game_state(game_state)
        self.set_game_state(game_state)
        self.set_game_state(game_state)


