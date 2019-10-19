import numpy as np
from rlbot.agents.base_agent import SimpleControllerState

from rlbot.utils.structures.game_data_struct import Rotator, Vector3, PlayerInfo


class Drone:
    def __init__(self, index: int, team: int):
        self.index: int = index
        self.team: int = team
        self.pos: np.ndarray = np.zeros(3)
        self.rot: np.ndarray = np.zeros(3)
        self.vel: np.ndarray = np.zeros(3)
        self.boost: float = 0.0
        self.orient_m: np.ndarray = np.identity(3)
        self.ctrl: SimpleControllerState = SimpleControllerState()

    def update(self, game_car: PlayerInfo):
        self.pos = a3v(game_car.physics.location)
        self.rot = a3r(game_car.physics.rotation)
        self.vel = a3v(game_car.physics.velocity)
        self.boost = game_car.boost
        self.orient_m = orient_matrix(self.rot)

        # Reset ctrl every tick.
        self.ctrl = SimpleControllerState()


def slow_to_pos(drone, position):
    # Calculate distance and velocity.
    distance = np.linalg.norm(position - drone.pos)
    velocity = np.linalg.norm(drone.vel)
    # Calculates the target position in local coordinates.
    local_target = local(drone.orient_m, drone.pos, position)
    # Finds 2D angle to target. Positive is clockwise.
    angle = np.arctan2(local_target[1], local_target[0])

    def special_sauce(x, a):
        """Modified sigmoid to smooth out steering."""
        # Graph: https://www.geogebra.org/m/udfp2zcy
        return 2 / (1 + np.exp(a * x)) - 1

    # Calculates steer.
    drone.ctrl.steer = special_sauce(angle, -5)

    # Throttle controller.
    if abs(angle) > 2:
        # If I'm facing the wrong way, do a little drift.
        drone.ctrl.throttle = 1.0
        drone.ctrl.handbrake = True
    elif distance > 100:
        # A simple PD controller to stop at target.
        drone.ctrl.throttle = cap(0.3 * distance - 0.2 * velocity, -1.0, 1.0)
        if distance > 1000:
            drone.ctrl.boost = True


def turn_to_pos(drone, position, game_time):    
    # Wiggle rate per second.
    RATE = 0.2

    # Calculates the target position in local coordinates.
    local_target = local(drone.orient_m, drone.pos, position)
    # Finds 2D angle to target. Positive is clockwise.
    angle = np.arctan2(local_target[1], local_target[0])

    # Toggles forward.
    drone.forward = round(game_time / RATE) % 2

    # Wiggles forward and back switching the steer to rotate on the spot.
    if drone.forward:
        drone.ctrl.throttle = 0.5
        drone.ctrl.steer = cap(angle, -1, 1)
    else:
        drone.ctrl.throttle = -0.5
        drone.ctrl.steer = cap(-angle, -1, 1)


def fast_to_pos(drone, position):
    # Calculates the target position in local coordinates.
    local_target = local(drone.orient_m, drone.pos, position)
    # Finds 2D angle to target. Positive is clockwise.
    angle = np.arctan2(local_target[1], local_target[0])

    def special_sauce(x, a):
        """Modified sigmoid to smooth out steering."""
        # Graph: https://www.geogebra.org/m/udfp2zcy
        return 2 / (1 + np.exp(a * x)) - 1

    # Control towards hit position. Fully boosting.
    drone.ctrl.steer = special_sauce(angle, -5)
    drone.ctrl.throttle = 1.0
    drone.ctrl.boost = True


def local(A: np.ndarray, p0: np.ndarray, p1: np.ndarray) -> np.ndarray:
    """Transforms world coordinates into local coordinates.

    Arguments:
        A {np.ndarray} -- The local orientation matrix.
        p0 {np.ndarray} -- World x, y, and z coordinates of the start point for the vector.
        p1 {np.ndarray} -- World x, y, and z coordinates of the end point for the vector.

    Returns:
        np.ndarray -- Local x, y, and z coordinates.
    """
    return np.dot(A.T, p1 - p0)


def cap(value: float, minimum: float, maximum: float) -> float:
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


def a3l(l: list) -> np.ndarray:
    """Converts list to numpy array.

    Arguments:
        L {list} -- The list to convert containing 3 elemets.

    Returns:
        np.array -- Numpy array with the same contents as the list.
    """
    return np.array([l[0], l[1], l[2]])


def a3r(r: Rotator) -> np.ndarray:
    """Converts rotator to numpy array.

    Arguments:
        R {Rotator} -- Rotator class containing pitch, yaw, and roll.

    Returns:
        np.ndarray -- Numpy array with the same contents as the rotator.
    """
    return np.array([r.pitch, r.yaw, r.roll])


def a3v(v: Vector3) -> np.ndarray:
    """Converts vector3 to numpy array.

    Arguments:
        V {Vector3} -- Vector3 class containing x, y, and z.

    Returns:
        np.ndarray -- Numpy array with the same contents as the vector3.
    """
    return np.array([v.x, v.y, v.z])


def orient_matrix(R: np.ndarray) -> np.ndarray:
    """Converts from Euler angles to an orientation matrix.

    Arguments:
        R {np.ndarray} -- Pitch, yaw, and roll.

    Returns:
        np.ndarray -- Orientation matrix of shape (3, 3).
    """
    # Credits to chip https://samuelpmish.github.io/notes/RocketLeague/aerial_control/
    pitch: float = R[0]
    yaw: float = R[1]
    roll: float = R[2]

    CR: float = np.cos(roll)
    SR: float = np.sin(roll)
    CP: float = np.cos(pitch)
    SP: float = np.sin(pitch)
    CY: float = np.cos(yaw)
    SY: float = np.sin(yaw)

    A = np.zeros((3, 3))

    # front direction
    A[0, 0] = CP * CY
    A[1, 0] = CP * SY
    A[2, 0] = SP

    # right direction (should be left but for some reason it is weird)
    A[0, 1] = CY * SP * SR - CR * SY
    A[1, 1] = SY * SP * SR + CR * CY
    A[2, 1] = -CP * SR

    # up direction
    A[0, 2] = -CR * CY * SP - SR * SY
    A[1, 2] = -CR * SY * SP + SR * CY
    A[2, 2] = CP * CR

    return A
