"""Rocket League Classes"""

import numpy as np
from math import sin, cos

default_A = np.array([
    [1,0,0],
    [0,1,0],
    [0,0,1]
])

class Car:
    def __init__(self, index):
        self.index      = index
        self.pos        = np.zeros(3)
        self.rot        = np.zeros(3)
        self.vel        = np.zeros(3)
        self.ang_vel    = np.zeros(3)
        self.on_g       = False
        self.sonic      = False
        self.A          = np.zeros(3)
        self.turn_r     = 0.0
    
class Ball:
    def __init__(self):
        self.pos        = np.zeros(3)
        self.vel        = np.zeros(3)
        self.ang_vel    = np.zeros(3)
        self.last_t     = ""

class BoostPad:
    def __init__(self, index, pos):
        self.index      = index
        self.pos        = pos
        self.active     = True
        self.timer      = 0.0

class Circle:
    def __init__(self,r,centre,A=default_A):
        self.r      = r
        self.centre = centre
        self.x      = centre[0]
        self.y      = centre[1]
        self.z      = centre[2]
        self.A      = A

    def generate_points(self,n):
        """generates n evenly spaced points on the circle"""
        points = np.zeros((n+1,3))
        for i in range(n+1):
            theta = i * (2*np.pi / n)
            offset = np.array([self.r*cos(theta),self.r*sin(theta),0])
            point = self.centre + np.dot(offset, self.A)
            points[i] += point
        return points