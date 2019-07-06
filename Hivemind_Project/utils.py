'''Utilities (fuctions and classes) for Rocket League.'''

import numpy as np
from math import sin, cos
from scipy.interpolate import interp1d

# -----------------------------------------------------------

# CLASSES:

default_orient_m = np.array([
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
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
        self.boost      = 0.0
        self.orient_m   = default_orient_m
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

class Drone(Car):
    def __init__(self, index):
        super().__init__(index)
        self.role = None
        self.pizzatime = True

# -----------------------------------------------------------

# FUNCTIONS:

def sign(team):
    """Gives the sign for a calculation based on team.
    
    Arguments:
        team {int} -- 0 if Blue, 1 if Orange.
    
    Returns:
        int -- 1 if Blue, -1 if Orange
    """
    return 1 if team == 0 else -1


def a3l(L):
    """Converts list to numpy array.

    Arguments:
        L {list} -- The list to convert containing 3 elemets.

    Returns:
        np.array -- Numpy array with the same contents as the list.
    """
    return np.array([L[0], L[1], L[2]])


def a3r(R):
    """Converts rotator to numpy array.

    Arguments:
        R {dict} -- Rotator class containing pitch, yaw, and roll.

    Returns:
        np.array -- Numpy array with the same contents as the rotator.
    """
    return np.array([R.pitch, R.yaw, R.roll])


def a3v(V):
    """Converts vector3 to numpy array.

    Arguments:
        V {dict} -- Vector3 class containing x, y, and z.

    Returns:
        np.array -- Numpy array with the same contents as the vector3.
    """
    return np.array([V.x, V.y, V.z])


def orient_matrix(R):
    """Converts from Euler angles to an orientation matrix.

    Arguments:
        R {np.array} -- np.array containg pitch, yaw, and roll.

    Returns:
        np.array -- Orientation matrix of shape (3, 3).
    """
    pitch   = R[0]
    yaw     = R[1]
    roll    = R[2]

    CR = cos(roll)
    SR = sin(roll)
    CP = cos(pitch)
    SP = sin(pitch)
    CY = cos(yaw)
    SY = sin(yaw)

    A = np.zeros((3, 3))

    # front direction
    A[0][0] = CP * CY
    A[0][1] = CP * SY
    A[0][2] = SP

    # right direction
    A[1][0] = CY * SP * SR - CR * SY
    A[1][1] = SY * SP * SR + CR * CY
    A[1][2] = -CP * SR

    # up direction
    A[2][0] = -CR * CY * SP - SR * SY
    A[2][1] = -CR * SY * SP + SR * CY
    A[2][2] = CP * CR

    return A


def local(V, A):
    """Transforms world coordinates into local coordinates.

    Arguments:
        V {np.array} -- Numpy array containing world x, y, and z coordinates.
        A {np.array} -- Numpy array containing the local orientation matrix.

    Returns:
        np.array -- Numpy array of local x, y, and z.
    """
    return np.dot(A, V)


def world(V, A):
    """Transforms local into world coordinates.

    Arguments:
        V {np.array} -- Numpy array containing local x, y, and z coordinates.
        A {np.array} -- Numpy array containing the local orientation matrix.

    Returns:
        np.array -- Numpy array of world x, y, and z.
    """
    return np.dot(V, A)


def get_steer(v, r):
    """Aproximated steer for a desired radius of turn and known velocity.

    Arguments:
        v {np.array} -- Numpy array containing a velocity vector.
        r {float} -- The desired radius of turn.

    Returns:
        float -- The magnitude of steering needed for the turn. If turn is impossible, is 1.
    """
    # Interpolation of the graph for max curvature given speed.
    s = np.array([0, 500, 1000, 1500, 1750, 2300])
    k = np.array([0.0069, 0.00396, 0.00235, 0.001375, 0.0011, 0.00088])
    f = interp1d(s, k)

    # Maximum curvature possible given velocity.
    max_k = f(np.linalg.norm(v))

    # Curvature of the desired radius of turn.
    want_k = 1 / r

    # Checks if turn is possible.
    if max_k >= want_k:
        # Curvature is roughly proportional to steer.
        return want_k / max_k
    else:
        return 1.0


def turn_r(v):
    """Calculates the minimum turning radius for given velocity.

    Arguments:
        v {np.array} -- Numpy array containing a velocity vector.

    Returns:
        float -- The smallest radius possible for the given velocity.
    """
    s = np.linalg.norm(v)
    return -6.901E-11 * s**4 + 2.1815E-07 * s**3 - 5.4437E-06 * s**2 + 0.12496671 * s + 157

# Bezier
# Currently reconsidering.
'''
def bezier_quadratic(p0, p1, p2, t):
    """Returns a position on bezier curve defined by 3 points at t.

    Arguments:
        p0 {np.array} -- Numpy array containg coordinates of point 0.
        p1 {np.array} -- Numpy array containg coordinates of point 1.
        p2 {np.array} -- Numpy array containg coordinates of point 2.
        t {float} -- A number between 0 and 1. 0 is the start of the curve, 1 is the end.

    Returns:
        np.array -- Numpy array containing the coordinates on the curve.
    """
    return p1 + (1-t)**2*(p0-p1) + t**2*(p2-p1)


def bezier_cubic(p0, p1, p2, p3, t):
    """Returns a position on bezier curve defined by 4 points at t.

    Arguments:
        p0 {np.array} -- Numpy array containg coordinates of point 0.
        p1 {np.array} -- Numpy array containg coordinates of point 1.
        p2 {np.array} -- Numpy array containg coordinates of point 2.
        p4 {np.array} -- Numpy array containg coordinates of point 3.
        t {float} -- A number between 0 and 1. 0 is the start of the curve, 1 is the end.

    Returns:
        np.array -- Numpy array containing the coordinates on the curve.
    """
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3
'''

# OGH curves (Optimised geometric hermite curves)
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.104.1622&rep=rep1&type=pdf