'''Rocket League data processing.'''

from utils import np, Car, Ball, BoostPad, Prediction, a3l, a3r, a3v, orient_matrix, turn_r

def setup(self, packet, field_info):
    """Sets up the variables and classes for the agent.
    
    Arguments:
        self {Calculator} -- The agent.
        packet {GameTickPacket} -- Information about the game.
        field_info {FieldInfoPacket} -- Information about the game field.
    """

    # Game info
    self.game_time  = packet.game_info.seconds_elapsed
    self.dt         = 1.0 / 120.0
    self.last_time  = 0.0
    self.r_active   = packet.game_info.is_round_active
    self.ko_pause   = packet.game_info.is_kickoff_pause
    self.m_ended    = packet.game_info.is_match_ended
    self.gravity    = packet.game_info.world_gravity_z

    # Creates Car objects for each car.
    self.teammates  = []
    self.opponents  = []
    for index in range(packet.num_cars):
        car = packet.game_cars[index]
        if index == self.index:
            self.player = Car(self.index, self.team, self.name)
        elif car.team == self.team:
            self.teammates.append(Car(index, car.team, car.name))
        else:
            self.opponents.append(Car(index, car.team, car.name))
    
    # Creates a Ball object.
    self.ball = Ball()

    # Creates Boostpad objects.
    self.l_pads = []
    self.s_pads = []
    for i in range(field_info.num_boosts):
        pad = field_info.boost_pads[i]
        pad_type = self.l_pads if pad.is_full_boost else self.s_pads
        pad_obj = BoostPad(i, a3v(pad.location))
        pad_type.append(pad_obj)


def process(self, packet):
    """Processes the gametick packet.

    Arguments:
        self {Calculator} -- The agent.
        packet {GameTickPacket} -- The game packet being processed.
    """

    # Processing game info.
    self.game_time  = packet.game_info.seconds_elapsed
    self.dt         = self.game_time - self.last_time
    self.last_time  = self.game_time
    self.r_active   = packet.game_info.is_round_active
    self.ko_pause   = packet.game_info.is_kickoff_pause
    self.m_ended    = packet.game_info.is_match_ended
    self.gravity    = packet.game_info.world_gravity_z

    # Processing drone data.
        # From packet:
    self.player.pos      = a3v(packet.game_cars[self.player.index].physics.location)
    self.player.rot      = a3r(packet.game_cars[self.player.index].physics.rotation)
    self.player.vel      = a3v(packet.game_cars[self.player.index].physics.velocity)
    self.player.ang_vel  = a3v(packet.game_cars[self.player.index].physics.angular_velocity)
    self.player.dead     = packet.game_cars[self.player.index].is_demolished
    self.player.wheel_c  = packet.game_cars[self.player.index].has_wheel_contact
    self.player.sonic    = packet.game_cars[self.player.index].is_super_sonic
    self.player.jumped   = packet.game_cars[self.player.index].jumped
    self.player.d_jumped = packet.game_cars[self.player.index].double_jumped
    self.player.boost    = packet.game_cars[self.player.index].boost
        # Calculated:
    self.player.orient_m = orient_matrix(self.player.rot)
    self.player.turn_r   = turn_r(self.player.vel)

    '''
    # Processing teammates.
    for teammate in self.teammates:
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
    '''

    '''
    # Processing opponents.
    for opponent in self.opponents:
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
    '''

    # Processing Ball data.
    self.ball.pos       = a3v(packet.game_ball.physics.location)
    self.ball.rot       = a3r(packet.game_ball.physics.rotation)
    self.ball.vel       = a3v(packet.game_ball.physics.velocity)
    self.ball.ang_vel   = a3v(packet.game_ball.physics.angular_velocity)
    self.ball.last_touch = packet.game_ball.latest_touch

    # Processing ball prediction.
    ball_prediction = self.get_ball_prediction_struct()
    self.ball.predict.pos = np.array([[step.physics.location.x, step.physics.location.y, step.physics.location.z] for step in ball_prediction.slices])
    self.ball.predict.vel = np.array([[step.physics.velocity.x, step.physics.velocity.y, step.physics.velocity.z] for step in ball_prediction.slices])
    self.ball.predict.time = np.array([[step.game_seconds] for step in ball_prediction.slices])

    # Processing Boostpads.
    self.active_pads = []
    for pad in self.l_pads + self.s_pads:
        pad.active = packet.game_boosts[pad.index].is_active
        pad.timer = packet.game_boosts[pad.index].timer
        if pad.active == True:
            self.active_pads.append(pad)