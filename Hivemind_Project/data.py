'''Rocket League data processing.'''

from utils import *


def setup(s, p, fi, indices):
    """Sets up the variables and classes for the hivemind.
    
    Arguments:
        s {BotHelperProcess (self)} -- The hivemind.
        p {GameTickPacket} -- Information about the game
        fi {FieldInfoPacket} -- Information about the game field.
        indices {set} -- Set containing the indices of each agent the hivemind controls.
    """
    # Creates Drone objects.
    s.drones = []
    for index in indices:
        s.drones.append(Drone(index))

    # Initialises hivemind attributes.
    s.team = p.game_cars[s.drones[0].index].team
    s.strategy = None

    # Creates Car objects for teammates and opponents.
    s.teammates = []
    s.opponents = []
    for index in range(p.num_cars):
        if p.game_cars[index].team == s.team:
            s.teammates.append(Car(index))
        else:
            s.opponents.append(Car(index))
    
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


def process(s, p):
    """Processes the gametick packet.

    Arguments:
        s {BotHelperProcess (self)} -- The agent who is processing the packet.
        p {GameTickPacket} -- The game packet being processed.
    """

    # Processing drone data.
    for drone in s.drones:
        drone.pos       = a3v(p.game_cars[drone.index].physics.location)
        drone.rot       = a3r(p.game_cars[drone.index].physics.rotation)
        drone.vel       = a3v(p.game_cars[drone.index].physics.velocity)
        drone.ang_vel   = a3v(p.game_cars[drone.index].physics.angular_velocity)
        drone.on_g      = p.game_cars[drone.index].has_wheel_contact
        drone.sonic     = p.game_cars[drone.index].is_super_sonic
        drone.boost     = p.game_cars[drone.index].boost
        drone.orient_m  = orient_matrix(drone.rot)
        drone.turn_r    = turn_r(drone.vel)

    # Processing Ball data.
    s.ball.pos      = a3v(p.game_ball.physics.location)
    s.ball.vel      = a3v(p.game_ball.physics.velocity)
    s.ball.ang_vel  = a3v(p.game_ball.physics.angular_velocity)
    s.ball.last_t   = p.game_ball.latest_touch.player_name
    
    # TODO Process teammates.
    
    # TODO Process opponents.

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
