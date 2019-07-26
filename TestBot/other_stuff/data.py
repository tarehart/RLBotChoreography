'''Rocket League data processing.'''

from utils import Car, Ball, BoostPad, a3l, a3r, a3v, orient_matrix, turn_r

def setup(s, p):
    """Sets up the variables and classes for the hivemind.
    
    Arguments:
        s {BaseAgent} -- The hivemind bot helper process.
        p {GameTickPacket} -- Information about the game.
        fi {FieldInfoPacket} -- Information about the game field.
    """

    # Game info.
    fi          = s.get_field_info()
    s.dt        = 1 / 120.0
    s.last_time = 0.0

    # Creates Car objects for all bots.
    s.teammates = []
    s.opponents = []
    for index in range(p.num_cars):
        if index == s.index:
            s.agent = Car(s.index)
        elif p.game_cars[index].team == s.team:
            s.teammates.append(Car(index))
        else:
            s.opponents.append(Car(index))

    s.agent.controller = None
    
    # Creates a Ball object.
    s.ball = Ball()

    # Creates Boostpad objects.
    s.l_pads = []
    s.s_pads = []
    for i in range(fi.num_boosts):
        pad = fi.boost_pads[i]
        pad_type = s.l_pads if pad.is_full_boost else s.s_pads
        pad_obj = BoostPad(i, a3v(pad.location))
        pad_type.append(pad_obj)

    s.setup = True


def process(s, p):
    """Processes the gametick packet.

    Arguments:
        s {BaseAgent} -- The agent which is processing the packet.
        p {GameTickPacket} -- The game packet being processed.
    """

    # Processing game info.
    s.time      = p.game_info.seconds_elapsed
    s.dt        = s.time - s.last_time
    s.last_time = s.time
    s.r_active  = p.game_info.is_round_active
    s.ko_pause  = p.game_info.is_kickoff_pause
    s.m_ended   = p.game_info.is_match_ended


    # Processing agent data.
    s.agent.pos       = a3v(p.game_cars[s.agent.index].physics.location)
    s.agent.rot       = a3r(p.game_cars[s.agent.index].physics.rotation)
    s.agent.vel       = a3v(p.game_cars[s.agent.index].physics.velocity)
    s.agent.ang_vel   = a3v(p.game_cars[s.agent.index].physics.angular_velocity)
    s.agent.on_g      = p.game_cars[s.agent.index].has_wheel_contact
    s.agent.sonic     = p.game_cars[s.agent.index].is_super_sonic
    s.agent.boost     = p.game_cars[s.agent.index].boost
    s.agent.orient_m  = orient_matrix(s.agent.rot)
    s.agent.turn_r    = turn_r(s.agent.vel)
    

    # Processing teammates.
    for teammate in s.teammates:
        teammate.pos        = a3v(p.game_cars[teammate.index].physics.location)
        teammate.rot        = a3r(p.game_cars[teammate.index].physics.rotation)
        teammate.vel        = a3v(p.game_cars[teammate.index].physics.velocity)
        teammate.ang_vel    = a3v(p.game_cars[teammate.index].physics.angular_velocity)
        teammate.on_g       = p.game_cars[teammate.index].has_wheel_contact
        teammate.sonic      = p.game_cars[teammate.index].is_super_sonic
        teammate.boost      = p.game_cars[teammate.index].boost
        teammate.orient_m   = orient_matrix(teammate.rot)
        teammate.turn_r     = turn_r(teammate.vel)

    # Processing opponents.
    for opponent in s.opponents:
        opponent.pos        = a3v(p.game_cars[opponent.index].physics.location)
        opponent.rot        = a3r(p.game_cars[opponent.index].physics.rotation)
        opponent.vel        = a3v(p.game_cars[opponent.index].physics.velocity)
        opponent.ang_vel    = a3v(p.game_cars[opponent.index].physics.angular_velocity)
        opponent.on_g       = p.game_cars[opponent.index].has_wheel_contact
        opponent.sonic      = p.game_cars[opponent.index].is_super_sonic
        opponent.boost      = p.game_cars[opponent.index].boost
        opponent.orient_m   = orient_matrix(opponent.rot)
        opponent.turn_r     = turn_r(opponent.vel)

    # Processing Ball data.
    s.ball.pos      = a3v(p.game_ball.physics.location)
    s.ball.vel      = a3v(p.game_ball.physics.velocity)
    s.ball.ang_vel  = a3v(p.game_ball.physics.angular_velocity)
    s.ball.predict  = s.get_ball_prediction_struct()

    # Processing Boostpads.
    s.active_pads = []
    for pad_type in (s.l_pads, s.s_pads):
        for pad in pad_type:
            pad.active = p.game_boosts[pad.index].is_active
            pad.timer = p.game_boosts[pad.index].timer
            if pad.active == True:
                s.active_pads.append(pad)