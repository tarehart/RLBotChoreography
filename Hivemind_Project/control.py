'''Drone control.'''

import numpy as np
from utils import a3l, local, cap, normalise


'''
Controller inputs:
    throttle:   float; ## -1 for full reverse, 1 for full forward.
    steer:      float; ## -1 for full left, 1 for full right.
    pitch:      float; ## -1 for nose down, 1 for nose up.
    yaw:        float; ## -1 for full left, 1 for full right.
    roll:       float; ## -1 for roll left, 1 for roll right.
    jump:       bool;  ## True if you want to press the jump button.
    boost:      bool;  ## True if you want to press the boost button.
    handbrake:  bool;  ## True if you want to press the handbrake button.
    use_item:   bool;  ## True if you want to use a rumble item.
'''

class Controller:
    """Base controller class. Is inherited from by other controllers."""
    def __init__(self):
        self.timer = 0.0

    def run(self, hive):
        """Runs the controller
        
        Arguments:
            hive {Hivemind} -- The hivemind.
        """
        # Increments timer.
        self.timer += hive.dt


class AngleBased(Controller):
    """Very basic controller which drives towards the target.

    Inheritance:
        Controller -- Base controller class. Is inherited from by other controllers.
    
    Behaviour:
        Throttle is always set to 1.
        If steering, always steers fully, i.e. either -1 or 1.
        Boosts when angle to target is below a certain threshold.
        Drifts if the angle to target is too large.

    Attributes:
        MIN_ANGLE -- Smallest angle at which it will steer.
        BOOST_ANGLE -- Boosting angle threshold.
        DRIFT_ANGLE -- Angle beyond which it will use handbrake.
    """
    def __init__(self):
        super().__init__()
        self.MIN_ANGLE = 0.1
        self.BOOST_ANGLE = 0.3
        self.DRIFT_ANGLE = 1.6

    def run(self, hive, drone, target):
        """Runs the controller.
        
        Arguments:
            hive {Hivemind} -- The hivemind.
            drone {Drone} -- Drone being controlled.
            target {np.ndarray} -- World coordinates of the point to drive towards.
        """
        # Calculates angle to target.
        local_target = local(drone.orient_m, drone.pos, target)
        angle = np.arctan2(local_target[1], local_target[0])

        # Creates controller inputs.
        if abs(angle) > self.MIN_ANGLE:
            drone.ctrl.steer = 1 if angle > 0 else -1

        if abs(angle) < self.BOOST_ANGLE:
            drone.ctrl.boost = True

        if abs(angle) > self.DRIFT_ANGLE:
            drone.ctrl.handbrake = True

        drone.ctrl.throttle = 1

        #super().run(hive) # Not needed here since this does not require a timer.


class TargetShot(AngleBased):
    """Simple shooting / dribbling controller.

    Credits to GooseFairy for the algorithm.
    Creates a target to drive towards by offsetting from the ball opposite
    as well as perpendicular to the wanted hit direction.
    
    Inheritance:
        AngleBased -- Very basic controller which drives towards the target.

    Attributes:
        PERP_DIST_COEFF {float} -- The perpendicular offset length (as a multiple of distance between the drone and ball)
        DIRECT_DIST_COEFF {float} -- In hit direction offest length (as a multiple of distance between the drone and ball)
    """
    def __init__(self):
        super().__init__()
        self.PERP_DIST_COEFF = 1/6
        self.DIRECT_DIST_COEFF = 1/2

    def run(self, hive, drone, target):
        """Runs the controller.
        
        Arguments:
            hive {Hivemind} -- The hivemind.
            drone {Drone} -- Drone being controlled.
            target {np.ndarray} -- World coordinates of where we want to hit the ball.
        """
        # Calculate drone's distance to ball.
        distance = np.linalg.norm(hive.ball.pos - drone.pos)

        # Find directions based on where we want to hit the ball.
        direction_to_hit = normalise(target - hive.ball.pos)
        perpendicular_to_hit = np.cross(direction_to_hit, a3l([0,0,1]))

        # Calculating component lengths and multiplying with direction.
        perpendicular_component = perpendicular_to_hit * cap(np.dot(perpendicular_to_hit, hive.ball.pos), -distance * self.PERP_DIST_COEFF, distance * self.PERP_DIST_COEFF)
        in_direction_component = -direction_to_hit * distance * self.DIRECT_DIST_COEFF

        # Combine components to get a drive target.
        drive_target = hive.ball.pos + in_direction_component + perpendicular_component

        super().run(hive, drone, drive_target)


class Dodge(Controller):
    # TODO Add a docstring to Dodge
    def __init__(self):
        super().__init__()
        self.FST_JUMP_DURATION = 0.1
        self.SND_JUMP_DELAY = 0.05
        self.SND_JUMP_DURATION = 2 - self.FST_JUMP_DURATION - self.SND_JUMP_DELAY
        
    def run(self, hive, drone, target):
        # TODO Docstring for run() and comments.

        local_target = local(drone.orient_m, drone.pos, target)
        direction = normalise(local_target)

        if self.timer <= self.FST_JUMP_DURATION:
            drone.ctrl.jump = True
        
        if self.timer >= self.FST_JUMP_DURATION + self.SND_JUMP_DELAY:
            drone.ctrl.jump = True
            drone.ctrl.pitch = -direction[0]
            drone.ctrl.paw = direction[1]

        if self.timer >= self.FST_JUMP_DURATION + self.SND_JUMP_DELAY + self.SND_JUMP_DURATION:
            drone.controller = None

        super().run(hive)


# TODO Half flips and diagonal dodging
# https://www.youtube.com/watch?v=pX950bhGhJE