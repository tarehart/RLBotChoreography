'''Controllers and Actions; this is where the actual output is generated.'''

import numpy as np
from utils import local


# -----------------------------------------------------------

# PARAMETERS:

# Angle Based Control
AB_MIN_ANGLE = 0.1
AB_DRIFT_ANGLE = 2.0
AB_DODGE_DIS = 500

# -----------------------------------------------------------

# CONTROLLERS:

def AB_control(drone, target):
    """Angle Based Control.
    Turns towards the target.
    Uses handbrake if the angle is too great.
    Dodges forward if it is facing the target and has space.
    
    Arguments:
        drone {Drone} -- Drone object which is being controlled.
        target {np.array} -- The x, y, and z coordinates of the target.
    """
    # Find the vector towards the target in local coordinates.
    local_target = local(drone.orient_m, drone.pos, target)
    # Find the clockwise angle to the target on the horizontal plane of the car.
    angle = np.arctan2(local_target[1], local_target[0])

    # Turn if needed.
    if abs(angle) > AB_MIN_ANGLE:
        drone.ctrl.steer = 1 if angle > 0 else -1
    ###elif local_target[0] > AB_DODGE_DIS:
    ###    pass
    else:
        drone.ctrl.boost = True

    # Apply handbrake for hard turns.
    if abs(angle) > AB_DRIFT_ANGLE:
        drone.ctrl.handbrake = True

    drone.ctrl.throttle = 1


def PD_control(drone, path):
    pass

# -----------------------------------------------------------

# TODO Figure out how to do stuff.
# This TODO will probably stay here for a while because I never truly know what I'm doing.

'''
Current theory:

Strategy leads to Roles.
Roles and current strategy lead to controllers.
Controllers can use actions.

Strategies are Enums.
Roles are classes.
Controllers are functions.
Actions are functions.
'''