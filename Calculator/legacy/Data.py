"""Data Processing and Managment"""

from RLClasses  import Car, Ball, BoostPad
from RLFunc     import a3l, a3r, a3v, orient_matrix, turn_r

def init(s):
    """runs initialisation"""
    s.player         = Car(s.index)
    s.ball           = Ball()

    field_info  = s.get_field_info()

    s.l_pads    = []
    s.s_pads    = []

    for i in range(field_info.num_boosts):
        pad = field_info.boost_pads[i]
        pad_type = s.l_pads if pad.is_full_boost else s.s_pads
        pad_obj = BoostPad(i, a3v(pad.location))
        pad_type.append(pad_obj)

    s.dt            = 1 / 120.0
    s.last_time     = 0.0

    s.calc_index    = 0
    s.human         = False

def process(s, p):
    """processes gametick packet"""

    #calc_index
    i = 0
    for index in range(len(p.game_cars)):
        if 'Calculator' in p.game_cars[index].name:
            if index == s.index:
                s.calc_index = i
                break
            i += 1
            
    #player
    s.player.pos    = a3v(p.game_cars[s.index].physics.location)
    s.player.rot    = a3r(p.game_cars[s.index].physics.rotation)
    s.player.vel    = a3v(p.game_cars[s.index].physics.velocity)
    s.player.ang_vel= a3v(p.game_cars[s.index].physics.angular_velocity)
    s.player.on_g   = p.game_cars[s.index].has_wheel_contact
    s.player.sonic  = p.game_cars[s.index].is_super_sonic
    s.player.A      = orient_matrix(s.player.rot)
    s.player.turn_r = turn_r(s.player.vel)

    #ball
    s.ball.pos      = a3v(p.game_ball.physics.location)
    s.ball.vel      = a3v(p.game_ball.physics.velocity)
    s.ball.ang_vel  = a3v(p.game_ball.physics.angular_velocity)
    s.ball.last_t   = p.game_ball.latest_touch.player_name
    s.ball.predict  = s.get_ball_prediction_struct()


    #teammates
    s.teammates = []

    #opponents
    s.opponents = []

    #boost pads
    s.active_pads = []
    for pad_type in (s.l_pads, s.s_pads):
        for pad in pad_type:
            pad.active = p.game_boosts[pad.index].is_active
            pad.timer = p.game_boosts[pad.index].timer
            if pad.active == True:
                s.active_pads.append(pad)

    #game info
    s.time          = p.game_info.seconds_elapsed
    s.dt            = s.time - s.last_time
    s.last_time     = s.time
    s.r_active      = p.game_info.is_round_active
    s.ko_pause      = p.game_info.is_kickoff_pause
    s.m_ended       = p.game_info.is_match_ended