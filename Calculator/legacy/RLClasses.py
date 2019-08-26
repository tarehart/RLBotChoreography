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
        self.predict    = None

class BoostPad:
    def __init__(self, index, pos):
        self.index      = index
        self.pos        = pos
        self.active     = True
        self.timer      = 0.0