from util import *

def path(self):
    """renders path from guides in white"""
    self.renderer.begin_rendering("path")
    self.renderer.draw_polyline_3d(self.guides, self.renderer.white())
    self.renderer.end_rendering()


def debug(self):
    """prints debug info"""
    self.renderer.begin_rendering("debug")
    self.renderer.draw_string_2d(self.RLwindow[2]*0.75, 10, 2, 2, self.state, self.renderer.red())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 40, 1, 1, "targets: " + str(len(self.targets)), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 55, 1, 1, "guides: " + str(len(self.guides)), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 70, 1, 1, "desire radius: " + str(radius_from_points(self.guides[0],self.guides[1],self.guides[2])), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 85, 1, 1, "desire steer: " + str(get_steer(np.linalg.norm(self.player.vel),radius_from_points(self.guides[0],self.guides[1],self.guides[2]))), self.renderer.black())
    self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 100, 1, 1, "output steer: " + str(self.steer), self.renderer.black())
    self.renderer.end_rendering()

def targets(self):
    """renders all targets in blue"""
    self.renderer.begin_rendering("targets")
    for target in self.targets:
        self.renderer.draw_rect_3d(target, 10, 10, True, self.renderer.blue())
    self.renderer.end_rendering()


def turn_circles(self):
    """renders turning circles in cyan"""
    r = self.player.turn_r
    k = 30 #higher numbers result in a better looking circle, but too high lags the bot

    circleR = []
    centreR = np.array([0,r,0])
    for i in range(k):
        theta = (2/k) * math.pi * i
        point = centreR + np.array([r*math.sin(theta), -r*math.cos(theta), 0])
        point = self.player.pos + world(point,self.player.orientM)
        circleR.append(point)

    circleL = []
    centreL = np.array([0,-r,0])
    for i in range(k):
        theta = (2/k) * math.pi * i
        point = centreL + np.array([r*math.sin(theta), r*math.cos(theta), 0])
        point = self.player.pos + world(point,self.player.orientM)
        circleL.append(point)

    self.renderer.begin_rendering("turn circles")
    self.renderer.draw_polyline_3d(circleR, self.renderer.cyan())
    self.renderer.draw_polyline_3d(circleL, self.renderer.cyan())
    self.renderer.end_rendering()
