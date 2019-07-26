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

    # Game info
    hive.time       = 0.0
    hive.dt         = 1.0 / 120.0
    hive.last_time  = 0.0
    hive.r_active   = False
    hive.ko_pause   = False
    hive.m_ended    = False
    hive.gravity    = - 650.0

    # Hivemind attributes
    hive.team       = packet.game_cars[indices[0]].team
    hive.strategy   = None

    # Creates Car objects for each car.
    hive.drones     = []
    hive.teammates  = []
    hive.opponents  = []
    for index in range(packet.num_cars):
        name = packet.game_cars[index].name
        if index in indices:
            hive.drone.append(Drone(index, hive.team, name))
        elif packet.game_cars[index].team == hive.team:
            hive.teammates.append(Car(index, hive.team, name))
        else:
            hive.opponents.append(Car(index, (hive.team+1) % 2, name))
    
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
    hive.time       = packet.game_info.seconds_elapsed
    hive.dt         = hive.time - hive.last_time
    hive.last_time  = hive.time
    hive.r_active   = packet.game_info.is_round_active
    hive.ko_pause   = packet.game_info.is_kickoff_pause
    hive.m_ended    = packet.game_info.is_match_ended
    hive.gravity    = packet.game_info.world_gravity_z


    # Processing drone data.
    for drone in hive.drones:
        # From packet:
        drone.pos       = a3v(packet.game_cars[drone.index].physics.location)
        drone.rot       = a3r(packet.game_cars[drone.index].physics.rotation)
        drone.vel       = a3v(packet.game_cars[drone.index].physics.velocity)
        drone.ang_vel   = a3v(packet.game_cars[drone.index].physics.angular_velocity)
        drone.dead      = packet.game_cars[drone.index].is_demolished
        drone.wheel_c   = packet.game_cars[drone.index].has_wheel_contact
        drone.sonic     = packet.game_cars[drone.index].is_super_sonic
        drone.jumped    = packet.game_cars[drone.index].jumped
        drone.d_jumped  = packet.game_cars[drone.index].double_jumped
        drone.boost     = packet.game_cars[drone.index].boost
        # Calculated:
        drone.orient_m  = orient_matrix(drone.rot)
        drone.turn_r    = turn_r(drone.vel)

    
    # Processing teammates.
    for teammate in hive.teammates:
        # From packet:
        teammate.pos        = a3v(packet.game_cars[teammate.index].physics.location)
        teammate.rot        = a3r(packet.game_cars[teammate.index].physics.rotation)
        teammate.vel        = a3v(packet.game_cars[teammate.index].physics.velocity)
        teammate.ang_vel    = a3v(packet.game_cars[teammate.index].physics.angular_velocity)
        teammate.dead       = packet.game_cars[teammate.index].is_demolished
        teammate.wheel_c    = packet.game_cars[teammate.index].has_wheel_contact
        teammate.sonic      = packet.game_cars[teammate.index].is_super_sonic
        teammate.jumped     = packet.game_cars[teammate.index].jumped
        teammate.d_jumped   = packet.game_cars[teammate.index].double_jumped
        teammate.boost      = packet.game_cars[teammate.index].boost
        # Calculated:
        #teammate.orient_m   = orient_matrix(teammate.rot)
        #teammate.turn_r     = turn_r(teammate.vel)
        #teammate.predict    = None

    # Processing opponents.
    for opponent in hive.opponents:
        # From packet:
        opponent.pos        = a3v(packet.game_cars[opponent.index].physics.location)
        opponent.rot        = a3r(packet.game_cars[opponent.index].physics.rotation)
        opponent.vel        = a3v(packet.game_cars[opponent.index].physics.velocity)
        opponent.ang_vel    = a3v(packet.game_cars[opponent.index].physics.angular_velocity)
        opponent.dead       = packet.game_cars[opponent.index].is_demolished
        opponent.wheel_c    = packet.game_cars[opponent.index].has_wheel_contact
        opponent.sonic      = packet.game_cars[opponent.index].is_super_sonic
        opponent.jumped     = packet.game_cars[opponent.index].jumped
        opponent.d_jumped   = packet.game_cars[opponent.index].double_jumped
        opponent.boost      = packet.game_cars[opponent.index].boost
        # Calculated:
        #opponent.orient_m   = orient_matrix(opponent.rot)
        #opponent.turn_r     = turn_r(opponent.vel)
        #opponent.predict    = None

    # Processing Ball data.
    hive.ball.pos       = a3v(packet.game_ball.physics.location)
    hive.ball.rot       = a3r(packet.game_ball.physics.rotation)
    hive.ball.vel       = a3v(packet.game_ball.physics.velocity)
    hive.ball.ang_vel   = a3v(packet.game_ball.physics.angular_velocity)
    # Ball prediction is being updated in the main file, i.e. hivemind.py.

    # Processing Boostpads.
    hive.active_pads = []
    for pad in hive.l_pads + hive.s_pads:
        pad.active = packet.game_boosts[pad.index].is_active
        pad.timer = packet.game_boosts[pad.index].timer
        if pad.active == True:
            hive.active_pads.append(pad)