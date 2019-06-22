from RLUtilities.LinearAlgebra import vec3, norm, dot
import math

def debug(self):
    """prints debug info"""
    self.renderer.begin_rendering("debug")
    
    if self.RLwindow == [0]*4:
        self.renderer.draw_string_2d(20, 10, 2, 2, str(self.state), self.renderer.red())
        self.renderer.draw_string_2d(10, 40, 1, 1, "car pos: " + str(self.info.my_car.pos), self.renderer.black())
        self.renderer.draw_string_2d(10, 55, 1, 1, "timer: " + str(self.timer), self.renderer.black())
        self.renderer.draw_string_2d(10, 70, 1, 1, "target speed: " + str(self.target_speed), self.renderer.black())
        self.renderer.draw_string_2d(10, 85, 1, 1, "drift: " + str(self.drift), self.renderer.black())
        self.renderer.draw_string_2d(10, 100, 1, 1, "handbrake: " + str(self.controls.handbrake), self.renderer.black())
        if not self.target == None:
            forward_target  = dot(self.target - self.info.my_car.pos, self.info.my_car.theta)[0]
            right_target    = dot(self.target - self.info.my_car.pos, self.info.my_car.theta)[1]
            angle_to_target = math.atan2(right_target, forward_target)
            self.renderer.draw_string_2d(10, 115, 1, 1, "angle to target: " + str(angle_to_target), self.renderer.black())
            self.renderer.draw_string_2d(10, 130, 1, 1, "forwd to target: " + str(forward_target), self.renderer.black())
            self.renderer.draw_string_2d(10, 145, 1, 1, "right to target: " + str(right_target), self.renderer.black())
    
    else:
        self.renderer.draw_string_2d(self.RLwindow[2]*0.7, 10, 2, 2, str(self.state), self.renderer.red())
        self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 40, 1, 1, "car pos: " + str(self.info.my_car.pos), self.renderer.black())
        self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 55, 1, 1, "timer: " + str(self.timer), self.renderer.black())
        self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 70, 1, 1, "target speed: " + str(self.target_speed), self.renderer.black())
        self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 85, 1, 1, "drift: " + str(self.drift), self.renderer.black())
        self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 100, 1, 1, "handbrake: " + str(self.controls.handbrake), self.renderer.black())
        if not self.target == None:
            forward_target  = dot(self.target - self.info.my_car.pos, self.info.my_car.theta)[0]
            right_target    = dot(self.target - self.info.my_car.pos, self.info.my_car.theta)[1]
            angle_to_target = math.atan2(right_target, forward_target)
            self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 115, 1, 1, "angle to target: " + str(angle_to_target), self.renderer.black())
            self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 130, 1, 1, "forwd to target: " + str(forward_target), self.renderer.black())
            self.renderer.draw_string_2d(self.RLwindow[2]*0.65, 145, 1, 1, "right to target: " + str(right_target), self.renderer.black())

    self.renderer.end_rendering()


def target(self):
    """renders target in blue"""
    self.renderer.begin_rendering("target")
    self.renderer.draw_rect_3d(self.target, 10, 10, True, self.renderer.blue())
    self.renderer.end_rendering()


def turn_circles(self):
    """renders turning circles in cyan"""
    speed = norm(self.info.my_car.vel)
    r = -6.901E-11 * speed**4 + 2.1815E-07 * speed**3 - 5.4437E-06 * speed**2 + 0.12496671 * speed + 157
    k = self.turn_c_quality

    circleR = []
    centreR = vec3(0,r,0)
    for i in range(k):
        theta = (2/k) * math.pi * i
        point = centreR + vec3(r*math.sin(theta), -r*math.cos(theta), 0)
        point = self.info.my_car.pos + dot(self.info.my_car.theta, point)
        circleR.append(point)

    circleL = []
    centreL = vec3(0,-r,0)
    for i in range(k):
        theta = (2/k) * math.pi * i
        point = centreL + vec3(r*math.sin(theta), r*math.cos(theta), 0)
        point = self.info.my_car.pos + dot(self.info.my_car.theta, point)
        circleL.append(point)

    self.renderer.begin_rendering("turn circles")
    self.renderer.draw_polyline_3d(circleR, self.renderer.cyan())
    self.renderer.draw_polyline_3d(circleL, self.renderer.cyan())
    self.renderer.end_rendering()