from util import *

def path(self):
    desire_radius   = radius_from_points(self.guides[0],self.guides[1],self.guides[2])

    if self.player.turn_r > desire_radius:
        self.handbrake = 1.0
    else:
        self.handbrake = 0.0

    if local(self.guides[0]-self.player.pos, self.player.orientM)[1] > 0.0:
        sign = 1
    else:
        sign = -1

    self.steer      = sign*get_steer(np.linalg.norm(self.player.vel), desire_radius)
    self.throttle   = 0.1
    self.boost      = 1.0

    if dist2d(self.guides[0], self.player.pos) <= 20.0:
        del self.guides[0]

#TODO Follow path

def kickoff(self):
    pass
#TODO Do a kickoff