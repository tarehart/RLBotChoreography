'''Rocket League data processing.'''

from utils import Car, Ball, BoostPad, Drone, a3l, a3r, a3v, orient_matrix, turn_r


def setup(hive, packet, field_info, indices):
    """Sets up the variables and classes for the hivemind.
    
    Arguments:
        hive {Hivemind} -- The hivemind bot helper process.
        packet {GameTickPacket} -- Information about the game.
        field_info {FieldInfoPacket} -- Information about the game field.
        indices {set} -- Set containing the indices of each agent the hivemind controls.
    """

    # Game info.
    hive.dt            = 1 / 120.0
    hive.last_time     = 0.0

    # Creates Drone objects.
    hive.drones = []
    for index in indices:
        hive.drones.append(Drone(index))

    # Initialises hivemind attributes.
    hive.team = packet.game_cars[hive.drones[0].index].team
    hive.strategy = None

    # Creates Car objects for teammates and opponents.
    hive.teammates = []
    hive.opponents = []
    for index in range(packet.num_cars):
        if index not in indices:
            if packet.game_cars[index].team == hive.team:
                hive.teammates.append(Car(index))
            else:
                hive.opponents.append(Car(index))
    
    # Creates a Ball object.
    hive.ball = Ball()

    # Creates Boostpad objects.
    hive.l_pads = []
    hive.s_pads = []
    for i in range(field_info.num_boosts):
        pad = field_info.boost_pads[i]
        pad_type = hive.l_pads if pad.is_full_boost else hive.s_pads
        pad_obj = BoostPad(i, a3v(pad.location))
        pad_type.append(pad_obj)


def process(hive, packet):
    """Processes the gametick packet.

    Arguments:
        hive {Hivemind} -- The process which is processing the packet.
        packet {GameTickPacket} -- The game packet being processed.
    """

    # Processing game info.
    hive.time      = packet.game_info.seconds_elapsed
    hive.dt        = hive.time - hive.last_time
    hive.last_time = hive.time
    hive.r_active  = packet.game_info.is_round_active
    hive.ko_pause  = packet.game_info.is_kickoff_pause
    hive.m_ended   = packet.game_info.is_match_ended


    # Processing drone data.
    for drone in hive.drones:
        drone.pos       = a3v(packet.game_cars[drone.index].physics.location)
        drone.rot       = a3r(packet.game_cars[drone.index].physics.rotation)
        drone.vel       = a3v(packet.game_cars[drone.index].physics.velocity)
        drone.ang_vel   = a3v(packet.game_cars[drone.index].physics.angular_velocity)
        drone.wheel_c      = packet.game_cars[drone.index].has_wheel_contact
        drone.sonic     = packet.game_cars[drone.index].is_super_sonic
        drone.boost     = packet.game_cars[drone.index].boost
        drone.orient_m  = orient_matrix(drone.rot)
        drone.turn_r    = turn_r(drone.vel)
    
    # Processing teammates.
    for teammate in hive.teammates:
        teammate.pos        = a3v(packet.game_cars[teammate.index].physics.location)
        teammate.rot        = a3r(packet.game_cars[teammate.index].physics.rotation)
        teammate.vel        = a3v(packet.game_cars[teammate.index].physics.velocity)
        teammate.ang_vel    = a3v(packet.game_cars[teammate.index].physics.angular_velocity)
        teammate.wheel_c       = packet.game_cars[teammate.index].has_wheel_contact
        teammate.sonic      = packet.game_cars[teammate.index].is_super_sonic
        teammate.boost      = packet.game_cars[teammate.index].boost
        #teammate.orient_m   = orient_matrix(teammate.rot)
        #teammate.turn_r     = turn_r(teammate.vel)

    # Processing opponents.
    for opponent in hive.opponents:
        opponent.pos        = a3v(packet.game_cars[opponent.index].physics.location)
        opponent.rot        = a3r(packet.game_cars[opponent.index].physics.rotation)
        opponent.vel        = a3v(packet.game_cars[opponent.index].physics.velocity)
        opponent.ang_vel    = a3v(packet.game_cars[opponent.index].physics.angular_velocity)
        opponent.wheel_c       = packet.game_cars[opponent.index].has_wheel_contact
        opponent.sonic      = packet.game_cars[opponent.index].is_super_sonic
        opponent.boost      = packet.game_cars[opponent.index].boost
        #opponent.orient_m   = orient_matrix(opponent.rot)
        #opponent.turn_r     = turn_r(opponent.vel)

    # Processing Ball data.
    hive.ball.pos      = a3v(packet.game_ball.physics.location)
    hive.ball.vel      = a3v(packet.game_ball.physics.velocity)
    hive.ball.ang_vel  = a3v(packet.game_ball.physics.angular_velocity)
    # Ball prediction is being updated in the main file, i.e. hivemind.py.

    # Processing Boostpads.
    hive.active_pads = []
    for pad_type in (hive.l_pads, hive.s_pads):
        for pad in pad_type:
            pad.active = packet.game_boosts[pad.index].is_active
            pad.timer = packet.game_boosts[pad.index].timer
            if pad.active == True:
                hive.active_pads.append(pad)