from util import *

class Car:
    def __init__(self, index):
        self.index      = index
        self.pos        = np.zeros((3,3))
        self.rot        = np.zeros((3,3))
        self.vel        = np.zeros((3,3))
        self.ang_vel    = np.zeros((3,3))
        self.onG        = False
        self.sonic      = False
        self.orientM    = np.zeros((3,3))
    
class Ball:
    def __init__(self):
        self.pos        = np.zeros((3,3))
        self.vel        = np.zeros((3,3))
        self.ang_vel    = np.zeros((3,3))
        self.turn_r     = 0.0

class BoostPad:
    def __init__(self, index, pos):
        self.index      = index
        self.pos        = pos
        self.is_active  = True
        self.timer      = 0.0

def init(self):
    self.throttle       = 0.0
    self.steer          = 0.0
    self.pitch          = 0.0
    self.yaw            = 0.0
    self.roll           = 0.0
    self.jump           = 0.0
    self.boost          = 0.0
    self.handbrake      = 0.0

    self.state          = None
    self.targets        = []

    field_info          = self.get_field_info()

    self.large_pads     = []
    self.small_pads     = []

    for i in range(field_info.num_boosts):
        pad = field_info.boost_pads[i]
        pad_type = self.large_pads if pad.is_full_boost else self.small_pads
        padobj = BoostPad(i, a3v(pad.location))
        pad_type.append(padobj)

def process(self, packet):
    """Processes packet"""

    #player
    self.player         = Car(self.index)
    self.player.pos     = a3v(packet.game_cars[self.index].physics.location)
    self.player.rot     = a3r(packet.game_cars[self.index].physics.rotation)
    self.player.vel     = a3v(packet.game_cars[self.index].physics.velocity)
    self.player.ang_vel = a3v(packet.game_cars[self.index].physics.angular_velocity)
    self.player.onG     = packet.game_cars[self.index].has_wheel_contact
    self.player.sonic   = packet.game_cars[self.index].is_super_sonic
    self.player.orientM = orientMat(self.player.rot)
    self.player.turn_r  = turning_radius(np.linalg.norm(self.player.vel))

    #ball
    self.ball           = Ball()
    self.ball.pos       = a3v(packet.game_ball.physics.location)
    self.ball.vel       = a3v(packet.game_ball.physics.velocity)
    self.ball.ang_vel   = a3v(packet.game_ball.physics.angular_velocity)

    #TODO opponents
    #opponent = Car(opponent index) ??

    #game info
    self.time               = packet.game_info.seconds_elapsed
    self.active             = packet.game_info.is_round_active
    self.ko_pause           = packet.game_info.is_kickoff_pause
    self.grav               = packet.game_info.world_gravity_z

    #boost pads
    self.active_pads = []
    for pad_type in (self.large_pads, self.small_pads):
        for pad in pad_type:
            pad.is_active   = packet.game_boosts[pad.index].is_active
            pad.timer       = packet.game_boosts[pad.index].timer
            if pad.is_active == True:
                self.active_pads.append(pad)
