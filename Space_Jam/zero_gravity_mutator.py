'''Run this file to enable microgravity. Have fun!'''

import time
from math import sin, cos

from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3

# PARAMETERS:

# How high the ball is on kickoff.
KICKOFF_BALL_HEIGHT = 700

# World Z gravity. Positive is upwards.
WORLD_GRAVITY = 1E-9 # Basically nothing.

# How much velocity gets applied when the car has wheel contact.
STICK = 0 # Negative values make you bounce.

class Observer():
    def __init__(self):
        self.game_interface = GameInterface(get_logger("observer"))
        self.game_interface.load_interface()
        self.game_interface.wait_until_loaded()
        self.game_interface.set_game_state(GameState(console_commands=[f'Set WorldInfo WorldGravityZ {WORLD_GRAVITY}']))
        self.main()

    def main(self):
        # Create packet
        packet = GameTickPacket()
        last_game_time = 0.0

        while True:
            # Update packet
            self.game_interface.update_live_data_packet(packet)
            game_time = packet.game_info.seconds_elapsed

            # Sleep until a new packet is received.
            if last_game_time == game_time:
                time.sleep(0.001)

            else:
                if packet.game_info.is_round_active:

                    # Renders ball prediction.
                    ball_prediction = BallPrediction()
                    self.game_interface.update_ball_prediction(ball_prediction)
                    self.game_interface.renderer.begin_rendering()
                    self.game_interface.renderer.draw_polyline_3d([step.physics.location for step in ball_prediction.slices[::10]], self.game_interface.renderer.cyan())
                    self.game_interface.renderer.end_rendering()

                    car_states = {}

                    for i in range(packet.num_cars):
                        car = packet.game_cars[i]

                        if STICK != 0 and car.has_wheel_contact:
                            # Makes cars stick by adding a velocity downwards.

                            pitch = car.physics.rotation.pitch
                            yaw = car.physics.rotation.yaw
                            roll = car.physics.rotation.roll

                            CP = cos(pitch) 
                            SP = sin(pitch)
                            CY = cos(yaw)
                            SY = sin(yaw)
                            CR = cos(roll)
                            SR = sin(roll)

                            x = car.physics.velocity.x - STICK*(-CR * CY * SP - SR * SY)
                            y = car.physics.velocity.y - STICK*(-CR * SY * SP + SR * CY)
                            z = car.physics.velocity.z - STICK*(CP * CR)

                            car_states.update({i: CarState(physics=Physics(velocity=Vector3(x,y,z)))})

                    
                    if packet.game_info.is_kickoff_pause and round(packet.game_ball.physics.location.z) != KICKOFF_BALL_HEIGHT:
                        # Places the ball in the air on kickoff.
                        ball_state = BallState(Physics(location=Vector3(z=KICKOFF_BALL_HEIGHT), velocity=Vector3(0,0,0)))

                        if len(car_states) > 0:
                            game_state = GameState(ball=ball_state, cars=car_states)
                        else:
                            game_state = GameState(ball=ball_state)

                    else:
                        if len(car_states) > 0:
                            game_state = GameState(cars=car_states)
                        else:
                            game_state = GameState()

                    # Uses state setting to set the game state.
                    self.game_interface.set_game_state(game_state)

if __name__ == "__main__":
    obv = Observer()