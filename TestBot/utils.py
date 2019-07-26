'''Utilities (fuctions and classes) for Rocket League.'''

from rlbot.utils.game_state_util import Vector3, Rotator

import numpy as np
from scipy.interpolate import interp1d

# -----------------------------------------------------------

# CLASSES:

class Car:
    """Houses the processed data from the packet for the cars.

    Attributes:
        index {int} -- The car's index in the packet.
        pos {np.ndarray} -- Position vector.
        rot {np.ndarray} -- Rotation (pitch, yaw, roll).
        vel {np.ndarray} -- Velocity vector.
        ang_vel {np.ndarray} -- Angular velocity (x, y, z). Chip's omega.
        dead {bool} -- Whether the car has been demolished.
        wheel_c {bool} -- Whether all four wheels are touching a surface.
        sonic {bool} -- Whether the car is supersonic.
        jumped {bool} -- Whether the car has jumped.
        d_jumped {bool} -- Whether the car has double jumped.
        name {str} -- Name of bot or human controlling the car.
        team {int} -- What team: 0 is blue, 1 is orange.
        boost {float} -- Amount of boost.

        orient_m {np.ndarray} -- A local orientation matrix. Chip's theta.
        turn_r {float} -- Turn radius.
        predict {dict} -- Predicted movement.
    """
    def __init__(self, index : int, team : int, name : str):
        self.index      : int           = index
        self.pos        : np.ndarray    = np.zeros(3)
        self.rot        : np.ndarray    = np.zeros(3)
        self.vel        : np.ndarray    = np.zeros(3)
        self.ang_vel    : np.ndarray    = np.zeros(3)
        self.dead       : bool          = False
        self.wheel_c    : bool          = False
        self.sonic      : bool          = False
        self.jumped     : bool          = False
        self.d_jumped   : bool          = False
        self.name       : str           = name
        self.team       : int           = team
        self.boost      : float         = 0.0
        
        self.orient_m   : np.ndarray    = np.identity(3)
        self.turn_r     : float         = 0.0
        self.predict    : dict          = {}

class Ball:
    """Houses the processed data from the packet for the ball.

    Attributes:
        pos {np.ndarray} -- Position vector.
        rot {np.ndarray} -- Rotation (pitch, yaw, roll). 
        vel {np.ndarray} -- Velocity vector.
        ang_vel {np.ndarray} -- Angular velocity (x, y, z). Chip's omega.
        predict {dict} -- Ball prediction.
    """
    def __init__(self):
        self.pos        : np.ndarray    = np.zeros(3)
        self.rot        : np.ndarray    = np.zeros(3)
        self.vel        : np.ndarray    = np.zeros(3)
        self.ang_vel    : np.ndarray    = np.zeros(3)
        self.predict    : dict          = {}

class BoostPad:
    """Houses the processed data from the packet fot the boost pads.

    Attributes:
        index {int} -- The pad's index.
        pos {np.ndarray} -- Position vector.
        active {bool} -- Whether the boost pad is active and can be collected.
        timer {float} -- How long until the boost pad is active again.
    """
    def __init__(self, index : int, pos : np.ndarray):
        self.index      : int           = index
        self.pos        : np.ndarray    = pos
        self.active     : bool          = True
        self.timer      : float         = 0.0

class Drone(Car):
    """A Drone is a Car under the hivemind's control.
    It has some additional attributes that Car does not have.
    
    Inheritance:
        Car -- Houses the processed data from the packet.

    Attributes:
        role {Role} -- The drone's role in a strategy.
        controller {Controller} -- The drone's controller generating inputs. 
    """
    def __init__(self, index : int, team : int, name : str):
        super().__init__(index, team, name)
        self.role       = None
        self.controller = None

# -----------------------------------------------------------

# FUNCTIONS FOR CONVERTION TO NUMPY ARRAYS:

def a3l(L : list) -> np.ndarray:
    """Converts list to numpy array.

    Arguments:
        L {list} -- The list to convert containing 3 elemets.

    Returns:
        np.array -- Numpy array with the same contents as the list.
    """
    return np.array([L[0], L[1], L[2]])


def a3r(R : Rotator) -> np.ndarray:
    """Converts rotator to numpy array.

    Arguments:
        R {Rotator} -- Rotator class containing pitch, yaw, and roll.

    Returns:
        np.ndarray -- Numpy array with the same contents as the rotator.
    """
    return np.array([R.pitch, R.yaw, R.roll])


def a3v(V : Vector3) -> np.ndarray:
    """Converts vector3 to numpy array.

    Arguments:
        V {Vector3} -- Vector3 class containing x, y, and z.

    Returns:
        np.ndarray -- Numpy array with the same contents as the vector3.
    """
    return np.array([V.x, V.y, V.z])


# -----------------------------------------------------------

# USEFUL UTILITY FUNCTIONS:

def normalise(V : np.ndarray) -> np.ndarray:
    """Normalises a vector.
    
    Arguments:
        V {np.ndarray} -- Vector.
    
    Returns:
        np.ndarray -- Normalised vector.
    """
    magnitude = np.linalg.norm(V)
    if magnitude != 0.0:
        return V / magnitude
    else:
        return V


def angle_between_vectors(v1 : np.ndarray, v2 : np.ndarray) -> float:
    """Returns the angle in radians between vectors v1 and v2.
    
    Arguments:
        v1 {np.ndarray} -- First vector.
        v2 {np.ndarray} -- Second vector
    
    Returns:
        float -- Positive acute angle between the vectors in radians.
    """
    v1_u = normalise(v1)
    v2_u = normalise(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def cap(value : float, minimum : float, maximum : float) -> float:
    """Caps the value at given minumum and maximum.
    
    Arguments:
        value {float} -- The value being capped.
        minimum {float} -- Smallest value.
        maximum {float} -- Largest value.
    
    Returns:
        float -- The capped value or the original value if within range.
    """
    if value > maximum:
        return maximum
    elif value < minimum:
        return minimum
    else:
        return value

# -----------------------------------------------------------

# FUNCTIONS FOR CONVERTING BETWEEN WORLD AND LOCAL COORDINATES:

def orient_matrix(R : np.ndarray) -> np.ndarray:
    """Converts from Euler angles to an orientation matrix.

    Arguments:
        R {np.ndarray} -- Pitch, yaw, and roll.

    Returns:
        np.ndarray -- Orientation matrix of shape (3, 3).
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
    A[0,0] = CP * CY
    A[1,0] = CP * SY
    A[2,0] = SP

    # right direction (should be left but for some reason it is weird)
    A[0,1] = CY * SP * SR - CR * SY
    A[1,1] = SY * SP * SR + CR * CY
    A[2,1] = -CP * SR

    # up direction
    A[0,2] = -CR * CY * SP - SR * SY
    A[1,2] = -CR * SY * SP + SR * CY
    A[2,2] = CP * CR

    return A


def local(A : np.ndarray, p0 : np.ndarray, p1 : np.ndarray) -> np.ndarray:
    """Transforms world coordinates into local coordinates.
    
    Arguments:
        A {np.ndarray} -- The local orientation matrix.
        p0 {np.ndarray} -- World x, y, and z coordinates of the start point for the vector.
        p1 {np.ndarray} -- World x, y, and z coordinates of the end point for the vector.
    
    Returns:
        np.ndarray -- Local x, y, and z coordinates.
    """
    return np.dot(A.T, p1 - p0)


def world(A : np.ndarray, p0 : np.ndarray, p1 : np.ndarray) -> np.ndarray:
    """Transforms local into world coordinates.
    
    Arguments:
        A {np.ndarray} -- The local orientation matrix.
        p0 {np.ndarray} -- World x, y, and z coordinates of the start point for the vector.
        p1 {np.ndarray} -- Local x, y, and z coordinates of the end point for the vector.
    
    Returns:
        np.ndarray -- World x, y, and z coordinates.
    """
    return p0 + np.dot(A, p1)

# -----------------------------------------------------------

# ROCKET LEAGUE SPECIFIC FUNCTIONS:

def team_sign(team : int) -> int:
    """Gives the sign for a calculation based on team.
    
    Arguments:
        team {int} -- 0 if Blue, 1 if Orange.
    
    Returns:
        int -- 1 if Blue, -1 if Orange
    """
    return 1 if team == 0 else -1
    

def turn_r(v : np.ndarray) -> float:
    """Calculates the minimum turning radius for given velocity.

    Arguments:
        v {np.ndarray} -- A velocity vector.

    Returns:
        float -- The smallest radius possible for the given velocity.
    """
    s = np.linalg.norm(v)
    return -6.901E-11 * s**4 + 2.1815E-07 * s**3 - 5.4437E-06 * s**2 + 0.12496671 * s + 157


def naive_predict(pos : np.ndarray, vel : np.ndarray, seconds : float, n : int) -> list:
    """Returns a list of tuples of time and position using a naive prediction method, i.e. continues moving at current velocity.
    
    Arguments:
        pos {np.ndarray} -- Starting position.
        vel {np.ndarray} -- Current velocity.
        seconds {float} -- Number of seconds to predict for.
        n {int} -- How many predictions to make.
    
    Returns:
        list -- List of tuples of time and predicted position at that time.
    """
    prediction = []
    step = seconds / n

    for i in range(n+1):
        t = step*i
        prediction.append((t, pos+t*vel))

    return prediction