'''
Import this file or just the function microgravity and run it somewhere in your bot every tick (e.g. in your get_output).
Pass in your bot and the GameTickPacket; all else is handles for you.

Enjoy microgravity!
'''

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3

def microgravity(agent, packet):
    """Enables microgravity. Cancels out bot downwards acceleration due to gravity using state_setting.
    
    Arguments:
        agent {BaseAgent} -- Your bot object. What this means for you: pass in self.
        packet {GameTickPacket} -- [description]
    """
    # Parameter:
    KICKOFF_BALL_HEIGHT = 1000

    # Finds delta time per tick.
    agent.zeroG_time = packet.game_info.seconds_elapsed
    try:
        dt = agent.zeroG_time - agent.zeroG_last_time
    except:
        dt = 1 / 120
    agent.zeroG_last_time = agent.zeroG_time

    # Calculates the acceleration due to gravity per tick.
    gravity = packet.game_info.world_gravity_z * dt

    # Cancels out gravity if the round is active.
    if packet.game_info.is_round_active:
        # Cancels out each car.
        car_states = {}
        for i in range(packet.num_cars):
            car = packet.game_cars[i].physics
            car_states.update({i : CarState(physics=Physics(velocity=Vector3(z = car.velocity.z - gravity)))})

        # Cancels out the ball.
        ball = packet.game_ball.physics
        if packet.game_info.is_kickoff_pause:
            # Places the ball in the air on kickoff.
            ball_state = BallState(Physics(location = Vector3(0,0,KICKOFF_BALL_HEIGHT), velocity=Vector3(z = ball.velocity.z - gravity)))
        else:
            ball_state = BallState(Physics(velocity=Vector3(z = ball.velocity.z - gravity)))

        # Uses state setting to set the game state.
        game_state = GameState(ball=ball_state, cars=car_states)
        # It doesn't hurt and apparently helps.
        agent.set_game_state(game_state)
        agent.set_game_state(game_state)
        agent.set_game_state(game_state)
        agent.set_game_state(game_state)
        agent.set_game_state(game_state)