from util import *

def state(self):
    """chooses state from situation"""
    #TODO
    if self.ko_pause:
        self.state = "kickoff"
    elif self.state == None:
        self.state = "plan"


def targets(self):
    #TODO pick targets
    self.targets = [self.ball.pos]


def path(self):
    """plans a bezier curve path from player to targets"""
    k = 50
    p0_ = self.player.pos
    p1_ = self.player.pos + world(np.array([self.player.turn_r,0,0]),self.player.orientM) * 2 #+ self.player.vel

    self.guides = []

    if len(self.targets) == 1:
        p2_ = self.targets[0]
        
        for i in range(k):
            self.guides.append(bezier_quadratic(p0_, p1_, p2_, (i+1)/k))

    else:
        p2_ = self.targets[0]+normalize(self.targets[0]-self.targets[1]) *100   #number not final; adjusts curve so that car ends up facing next target. TODO replace it with something dependent on situation.
        p3_ = self.targets[0]

        for i in range(k):
            self.guides.append(bezier_cubic(p0_, p1_, p2_, p3_,(i+1)/k))
    
    #might be useful for curvature constraints: https://hal.inria.fr/inria-00072572/document
    #centreR = self.player.pos + world(np.array([0,self.player.turn_r,0]),self.player.orientM)
    #centreL = self.player.pos + world(np.array([0,-self.player.turn_r,0]),self.player.orientM)


def path2d(self):
    """plans a bezier curve path from player to targets (2D)"""
    k = 50
    p0_ = self.player.pos
    p1_ = self.player.pos + world(np.array([self.player.turn_r,0,0]),self.player.orientM) * 2 #+ self.player.vel

    self.guides = []

    if len(self.targets) == 1:
        p2_ = self.targets[0]
        
        for i in range(k):
            self.guides.append(bezier_quadratic(a2(p0_), a2(p1_), a2(p2_), (i+1)/k))

    else:
        p2_ = self.targets[0]+normalize(self.targets[0]-self.targets[1]) *100   #number not final; adjusts curve so that car ends up facing next target. TODO replace it with something dependent on situation.
        p3_ = self.targets[0]

        for i in range(k):
            self.guides.append(bezier_cubic(a2(p0_), a2(p1_), a2(p2_), a2(p3_),(i+1)/k))

        
def convboost(self):
    """adds convenient boost pads as targets and plans new path"""
    for guide in self.guides:
        for pad in self.active_pads:
            if pad not in self.plan_pads and dist3d(guide, pad.pos) <= 300:      #number not final; distance from guide to potential convenient boost has to be less or equal to this number. TODO replace it with something dependent on situation.
                self.plan_pads.append(pad)
                self.targets.insert(0,pad.pos)
                path(self)
                convboost(self)
                break
        else:
            continue
        break


def convboost2d(self):
    """adds convenient boost pads as targets and plans new path (2D)"""
    for guide in self.guides:
        for pad in self.active_pads:
            if pad not in self.plan_pads and dist2d(guide, pad.pos) <= 300:      #number not final; distance from guide to potential convenient boost has to be less or equal to this number. TODO replace it with something dependent on situation.
                self.plan_pads.append(pad)
                self.targets.insert(0,pad.pos)
                path2d(self)
                convboost2d(self)
                break
        else:
            continue
        break