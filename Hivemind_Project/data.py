'''Data processing.'''

from utils import *


def setup(s, indices, field_info):
    """Sets up the variables and classes for the hivemind.
    
    Arguments:
        s {BotHelperProcess (self)} -- The hivemind.
        indices {set} -- Set containing the indices of each agent the hivemind controls.
        field_info {FieldInfoPacket} -- Information about the game field.
    """
    # Creates Car and Ball objects which house all the related data.
    s.drones = []
    for index in indices:
        s.drones.append(Car(index))
    
    s.ball = Ball()

    # Creates Boostpad objects which house data related to boostpads.
    s.l_pads = []
    s.s_pads = []
    for i in range(field_info.num_boosts):
        pad = field_info.boost_pads[i]
        pad_type = s.l_pads if pad.is_full_boost else s.s_pads
        pad_obj = BoostPad(i, a3v(pad.location))
        pad_type.append(pad_obj)


def process(s, p):
    """Processes the gametick packet.

    Arguments:
        s {BotHelperProcess (self)} -- The agent who is processing the packet.
        p {GameTickPacket} -- The game packet being processed.
    """

    # Processing drone data.
    for drone in s.drones:
        drone.pos        = a3v(p.game_cars[drone.index].physics.location)
        drone.rot        = a3r(p.game_cars[drone.index].physics.rotation)
        drone.vel        = a3v(p.game_cars[drone.index].physics.velocity)
        drone.ang_vel    = a3v(p.game_cars[drone.index].physics.angular_velocity)
        drone.on_g       = p.game_cars[drone.index].has_wheel_contact
        drone.sonic      = p.game_cars[drone.index].is_super_sonic
        drone.orient_m   = orient_matrix(drone.rot)
        drone.turn_r     = turn_r(drone.vel)

    # Processing Ball data.
    s.ball.pos      = a3v(p.game_ball.physics.location)
    s.ball.vel      = a3v(p.game_ball.physics.velocity)
    s.ball.ang_vel  = a3v(p.game_ball.physics.angular_velocity)
    s.ball.last_t   = p.game_ball.latest_touch.player_name
    
    # TODO Process teammates.
    s.teammates = []

    # TODO Process opponents.
    s.opponents = []

    # Processing Boostpads.
    s.active_pads = []
    for pad_type in (s.l_pads, s.s_pads):
        for pad in pad_type:
            pad.active = p.game_boosts[pad.index].is_active
            pad.timer = p.game_boosts[pad.index].timer
            if pad.active == True:
                s.active_pads.append(pad)

    # Processing other game info.
    s.time      = p.game_info.seconds_elapsed
    s.r_active  = p.game_info.is_round_active
    s.ko_pause  = p.game_info.is_kickoff_pause
    s.m_ended   = p.game_info.is_match_ended
