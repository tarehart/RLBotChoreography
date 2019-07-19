import numpy as np
from utils import local, cap, normalise, angle_between_vectors


'''
throttle:   float; /// -1 for full reverse, 1 for full forward
steer:      float; /// -1 for full left, 1 for full right
pitch:      float; /// -1 for nose down, 1 for nose up
yaw:        float; /// -1 for full left, 1 for full right
roll:       float; /// -1 for roll left, 1 for roll right
jump:       bool;  /// true if you want to press the jump button
boost:      bool;  /// true if you want to press the boost button
handbrake:  bool;  /// true if you want to press the handbrake button
use_item:   bool;  /// true if you want to use a rumble item
'''

# PARAMETERS:

AB_MIN_ANGLE = 0.1
AB_BOOST_ANGLE = 0.3
AB_DRIFT_ANGLE = 1.6

GK_MIN_ANGLE = 0.2
GK_BACK_ANGLE = np.pi / 2
GK_THROTTLE = 0.01

LINE_PD_ALPHA = -1 / 1000
LINE_PD_BETA = 1 / (2*np.pi)
LINE_PD_BOOST_ANGLE = 0.2

DG_1_JUMP_DURATION = 0.05
DG_2_JUMP_DELAY = 0.05
DG_2_JUMP_DURATION = 2 - DG_1_JUMP_DURATION - DG_2_JUMP_DELAY

class AB_Control:
    def __init__(self, drone, target):
        self.drone = drone
        self.target = target

    def run(self):
        local_target = local(self.drone.orient_m, self.drone.pos, self.target)
        angle = np.arctan2(local_target[1], local_target[0])

        if abs(angle) > AB_MIN_ANGLE:
            self.drone.ctrl.steer = 1 if angle > 0 else -1

        if abs(angle) < AB_BOOST_ANGLE:
            self.drone.ctrl.boost = True

        if abs(angle) > AB_DRIFT_ANGLE:
            self.drone.ctrl.handbrake = True


        self.drone.ctrl.throttle = 1

class GK_Control:
    def __init__(self, drone, target):
        self.drone = drone
        self.target = target

    def run(self):
        local_target = local(self.drone.orient_m, self.drone.pos, self.target)
        angle = np.arctan2(local_target[1], local_target[0])

        if abs(angle) > GK_MIN_ANGLE or np.pi - abs(angle) > GK_MIN_ANGLE:
            self.drone.ctrl.steer = 1 if angle > 0 else -1

        distance = abs(local_target[0])
        
        if abs(angle) > GK_BACK_ANGLE:
            self.drone.ctrl.throttle = cap(-1 * GK_THROTTLE * distance, -1, 1)
        else:
            self.drone.ctrl.throttle = cap(1 * GK_THROTTLE * distance, -1, 1)


class LINE_PD_Control:
    def __init__(self, drone, p0, p1):
        self.drone = drone
        self.line = (p0, p1)

    def run(self):
        line_v = self.line[1]-self.line[0]
        theta = angle_between_vectors(line_v, self.line[1]-self.drone.pos)
        distance = np.linalg.norm(self.line[1] - self.drone.pos)
        print("theta", theta)
        phi = angle_between_vectors(line_v, self.drone.vel)
        print("phi", phi)

        self.drone.ctrl.throttle = 1
        self.drone.ctrl.steer = cap(LINE_PD_ALPHA * (np.sin(theta) * distance) + LINE_PD_BETA * phi, -1, 1)

        local_target = local(self.drone.orient_m, self.drone.pos, self.line[1])
        angle = np.arctan2(local_target[1], local_target[0])

        if abs(angle) < LINE_PD_BOOST_ANGLE:
            self.drone.ctrl.boost = True



class Dodge:
    def __init__(self, drone, direction):
        self.drone = drone
        self.direction = normalise(direction)

    def run(self, timer):
        self.drone.ctrl.boost + False

        if timer <= DG_1_JUMP_DURATION:
            self.drone.ctrl.jump = True
        
        if timer >= DG_1_JUMP_DURATION + DG_2_JUMP_DELAY:
            self.drone.ctrl.jump = True
            self.drone.ctrl.pitch = -self.direction[0]
            self.drone.ctrl.paw = self.direction[1]

        if timer >= DG_1_JUMP_DURATION + DG_2_JUMP_DELAY + DG_2_JUMP_DURATION:
            self.drone.controller = None