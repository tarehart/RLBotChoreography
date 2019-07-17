'''Controllers and Mechanics; this is where the actual output is generated.'''

import numpy as np
from utils import a3l, local, normalise


# -----------------------------------------------------------

# PARAMETERS:

# Dodge
FIRST_JUMP_DURATION = 0.1
SECOND_JUMP_DELAY = 0.15
DODGE_EXPIRE = 2.0

# Angle Based Control
AB_MIN_ANGLE = 0.2
AB_DODGE_DIS = 500
AB_BOOST_ANGLE = 0.4
AB_DRIFT_ANGLE = 1.5


# -----------------------------------------------------------

# MECHANICS:     

class Dodge:
    def __init__(self, target):
        self.timer = 0.0
        self.direction = normalise(target)

    def step(self, dt, drone):
        drone.ctrl.boost = False

        if self.timer < FIRST_JUMP_DURATION:
            print("first jump")
            drone.ctrl.jump = True
        elif self.timer - FIRST_JUMP_DURATION > SECOND_JUMP_DELAY:
            print("second jump")
            drone.ctrl.pitch = -self.direction[0]
            drone.ctrl.yaw = self.direction[1]
            drone.ctrl.jump = True
        else:
            print("not jumping")
            drone.ctrl.jump = False

        self.timer += dt

        if self.timer >= DODGE_EXPIRE:
            drone.mechanic = None


# -----------------------------------------------------------

# CONTROLLERS:

def AB_control(s, drone, target):
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

    '''
    # Dodge if not turning.
    elif local_target[0] > AB_DODGE_DIS:   
        if drone.mechanic == None:
            drone.mechanic = Dodge(local_target)

    # Step through Dodge.
    if isinstance(drone.mechanic, Dodge):
        drone.mechanic.step(s.dt, drone)
    '''

    # Boost if angle is small.
    if abs(angle) < AB_BOOST_ANGLE:
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
Actions are classes.
'''