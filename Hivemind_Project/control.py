'''Controllers and Mechanics; this is where the actual output is generated.'''

import numpy as np
from utils import a3l, local, normalise


# -----------------------------------------------------------

# PARAMETERS:

# Dodge
FIRST_JUMP_DURATION = 0.05
SECOND_JUMP_DELAY = 0.15
DODGE_EXPIRE = 2.0

# Kickoff
KO_MIN_ANGLE = 0.1
KO_TIME_BEFORE_HIT = 0.3

# Angle Based Control
AB_MIN_ANGLE = 0.15
AB_DODGE_DIS = 500
AB_BOOST_ANGLE = 0.4
AB_DRIFT_ANGLE = 1.6


# -----------------------------------------------------------

# MECHANICS:     

class Dodge:
    def __init__(self, target):
        self.timer = 0.0
        self.direction = normalise(target)

    def step(self, dt, drone):
        drone.ctrl.boost = False

        if self.timer < FIRST_JUMP_DURATION:
            drone.ctrl.jump = True
        elif self.timer - FIRST_JUMP_DURATION > SECOND_JUMP_DELAY:
            drone.ctrl.pitch = -self.direction[0]
            drone.ctrl.yaw = self.direction[1]
            drone.ctrl.jump = True
        else:
            drone.ctrl.jump = False

        self.timer += dt

        if self.timer >= DODGE_EXPIRE:
            drone.mechanic = None


# -----------------------------------------------------------

# CONTROLLERS:

def KO_control(s, drone):
    """Kickoff controller.
    Boosts and turns towards the ball.
    Dodges right before hitting the ball.
    
    Arguments:
        drone {Drone} -- Drone object which is being controlled.
        ball {Ball} -- Ball object which is being targetted for the kickoff.
    """
    target = s.ball.pos
    '''if np.linalg.norm(s.ball.pos - drone.pos) > KO_GOTO_PAD_DIS:
        print("going after pad")
        for pad in s.active_pads:
            if np.linalg.norm(pad.pos - drone.pos) < np.linalg.norm(target - drone.pos):
                target = pad.pos

    else:
        print("going after ball")'''
    # TODO Fix back kickoffs by taking boost or dodging.

    # Find the vector towards the target in local coordinates.
    local_target = local(drone.orient_m, drone.pos, target)
    # Find the clockwise angle to the target on the horizontal plane of the car.
    angle = np.arctan2(local_target[1], local_target[0])
    # Estimate time to hit the ball.
    time_to_hit = local_target[0] / np.linalg.norm(drone.vel)
    # If not dodging, dodge if about to hit, otherwise steer towards ball.
    if not isinstance(drone.mechanic, Dodge):
        if time_to_hit <= KO_TIME_BEFORE_HIT and all(target == s.ball.pos):
            drone.mechanic = Dodge(local_target)
        else:
            drone.ctrl.throttle = 1
            drone.ctrl.boost = True
            if abs(angle) > KO_MIN_ANGLE:
                drone.ctrl.steer = 1 if angle > 0 else -1
        


def AB_control(drone, target):
    """Angle Based Control.
    Turns towards the target.
    Uses handbrake if the angle is too great.
    
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
    # Boost if angle is small.
    if abs(angle) < AB_BOOST_ANGLE:
        drone.ctrl.boost = True
    # Apply handbrake for hard turns.
    if abs(angle) > AB_DRIFT_ANGLE:
        drone.ctrl.handbrake = True
    # Throttle is always on full.
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