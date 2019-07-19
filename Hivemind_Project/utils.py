'''Utilities (fuctions and classes) for Rocket League.'''

import numpy as np
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
        self.predict    = None

class Ball:
    def __init__(self):
        self.pos        = np.zeros(3)
        self.vel        = np.zeros(3)
        self.ang_vel    = np.zeros(3)
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
        self.role       = None
        self.mechanic   = None

# -----------------------------------------------------------

# FUNCTIONS:

def team_sign(team : int):
    """Gives the sign for a calculation based on team.
    
    Arguments:
        team {int} -- 0 if Blue, 1 if Orange.
    
    Returns:
        int -- 1 if Blue, -1 if Orange
    """
    return 1 if team == 0 else -1


def a3l(L : list):
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


def normalise(V):
    """Normalises a vector.
    
    Arguments:
        V {np.array} -- Vector.
    
    Returns:
        np.array -- Normalised vector.
    """
    magnitude = np.linalg.norm(V)
    if magnitude != 0.0:
        return V / magnitude
    else:
        return V


def cap(value, minimum, maximum):
    """Caps the value at given minumum and maximum.
    
    Arguments:
        value {float or int} -- The value being capped.
        minimum {float or int} -- Smallest value.
        maximum {float or int} -- Largest value.
    
    Returns:
        float or int -- The capped value or the original value if within range.
    """
    if value > maximum:
        return maximum
    elif value < minimum:
        return minimum
    else:
        return value


def orient_matrix(R):
    """Converts from Euler angles to an orientation matrix.

    Arguments:
        R {np.array} -- Pitch, yaw, and roll.

    Returns:
        np.array -- Orientation matrix of shape (3, 3).
    """
    # Credits to chip https://samuelpmish.github.io/notes/RocketLeague/aerial_control/
    pitch : float = R[0]
    yaw   : float = R[1]
    roll  : float = R[2]

    CR : float = np.cos(roll)
    SR : float = np.sin(roll)
    CP : float = np.cos(pitch)
    SP : float = np.sin(pitch)
    CY : float = np.cos(yaw)
    SY : float = np.sin(yaw)

    A = np.zeros((3, 3))

    # front direction
    A[0][0] = CP * CY
    A[1][0] = CP * SY
    A[2][0] = SP

    # right direction (should be left but for some reason it is weird)
    A[0][1] = CY * SP * SR - CR * SY
    A[1][1] = SY * SP * SR + CR * CY
    A[2][1] = -CP * SR

    # up direction
    A[0][2] = -CR * CY * SP - SR * SY
    A[1][2] = -CR * SY * SP + SR * CY
    A[2][2] = CP * CR

    return A


def local(A, p0, p1):
    """Transforms world coordinates into local coordinates.
    
    Arguments:
        A {np.array} -- The local orientation matrix.
        p0 {np.array} -- World x, y, and z coordinates of the start point for the vector.
        p1 {np.array} -- World x, y, and z coordinates of the end point for the vector.
    
    Returns:
        np.array -- Local x, y, and z coordinates.
    """
    return np.dot(A.T, p1 - p0)


def world(A, p0, p1):
    """Transforms local into world coordinates.
    
    Arguments:
        A {np.array} -- The local orientation matrix.
        p0 {np.array} -- World x, y, and z coordinates of the start point for the vector.
        p1 {np.array} -- Local x, y, and z coordinates of the end point for the vector.
    
    Returns:
        np.array -- World x, y, and z coordinates.
    """
    return p0 + np.dot(A, p1)


def naive_predict(car, s, n):
    """Predicts the car as if it was going to continue at current velocity in a straight line.
    
    Arguments:
        car {Car} -- The car object who's motion we want to predict.
        s {float} -- How many seconds to predict for.
        n {int} -- Number of predicted points (1 less than actual because that includes current position).
    
    Returns:
        [type] -- [description]
    """
    return [car.pos + car.vel*(t*s/n) for t in range(n+1)]


def turn_r(v):
    """Calculates the minimum turning radius for given velocity.

    Arguments:
        v {np.array} -- A velocity vector.

    Returns:
        float -- The smallest radius possible for the given velocity.
    """
    s = np.linalg.norm(v)
    return -6.901E-11 * s**4 + 2.1815E-07 * s**3 - 5.4437E-06 * s**2 + 0.12496671 * s + 157