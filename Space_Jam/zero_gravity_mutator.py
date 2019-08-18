'''Run this file to enable microgravity. Have fun!'''

import time

from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3

class Observer():
    def __init__(self):
        self.game_interface = GameInterface(get_logger("observer"))
        self.game_interface.load_interface()
        self.game_interface.wait_until_loaded()
        self.main()

    def main(self):
        # Create packet
        packet = GameTickPacket()
        last_game_time = 0.0

        while True:
            # Update packet
            self.game_interface.update_live_data_packet(packet)
            game_time = packet.game_info.seconds_elapsed

            if last_game_time == game_time:
                time.sleep(0.001)

            else:
                # Parameter:
                KICKOFF_BALL_HEIGHT = 700

                # Finds delta time per tick.
                try:
                    dt = game_time - last_game_time
                except:
                    dt = 1 / 120
                last_game_time = game_time

                # Calculates the acceleration due to gravity per tick.
                gravity = packet.game_info.world_gravity_z * dt

                # Cancels out gravity if the round is active.
                if packet.game_info.is_round_active:
                    # Cancels out each car.
                    car_states = {}
                    for i in range(packet.num_cars):
                        car = packet.game_cars[i].physics
                        if car.location.z > 20:
                            car_states.update(
                                {i: CarState(physics=Physics(velocity=Vector3(z=car.velocity.z - gravity)))})

                    # Cancels out the ball.
                    ball = packet.game_ball.physics

                    if packet.game_info.is_kickoff_pause and round(ball.location.z) != KICKOFF_BALL_HEIGHT:
                        # Places the ball in the air on kickoff.
                        ball_state = BallState(Physics(location=Vector3(z=KICKOFF_BALL_HEIGHT), velocity=Vector3(z=0)))
                    else:
                        ball_state = BallState(
                            Physics(velocity=Vector3(z=ball.velocity.z - gravity)))

                    # Uses state setting to set the game state.
                    game_state = GameState(ball=ball_state, cars=car_states)
                    self.game_interface.set_game_state(game_state)

if __name__ == "__main__":
    obv = Observer()    # nice.