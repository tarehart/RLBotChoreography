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
        MIN_ANGLE {float} -- Smallest angle at which it will steer.
        BOOST_ANGLE {float} -- Boosting angle threshold.
        DRIFT_ANGLE {float} -- Angle beyond which it will use handbrake.
    """
    def __init__(self):
        super().__init__()
        self.MIN_ANGLE = 0.05
        self.BOOST_ANGLE = 0.3
        self.DRIFT_ANGLE = 1.8

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
    """Simple dodge controller. Dodges towards a target.
    
    Inheritance:
        Controller -- Base controller class. Is inherited from by other controllers.

    Behaviour:
        Jumps, waits, dodges in the direction of the target, waits, expires.

    Attributes:
        FST_JUMP_DURATION {float} -- The duration of the first jump.
        SND_JUMP_DELAY {float} -- The delay between the first and second jump.
        SND_JUMP_DURATION {float} -- The duration of the dodge after the second jump.
    """
    def __init__(self):
        super().__init__()
        self.FST_JUMP_DURATION = 0.1
        self.SND_JUMP_DELAY = 0.1
        self.SND_JUMP_DURATION = 1.5 - self.FST_JUMP_DURATION - self.SND_JUMP_DELAY
        
    def run(self, hive, drone, target):
        """Runs the controller.
        
        Arguments:
            hive {Hivemind} -- The hivemind.
            drone {Drone} -- Drone being controlled.
            target {np.ndarray} -- World coordinates of where to dodge towards.
        """
        # Calculates local target and direction.
        local_target = local(drone.orient_m, drone.pos, target)
        direction = normalise(local_target)

        # First jump
        if self.timer <= self.FST_JUMP_DURATION:
            drone.ctrl.jump = True
        
        # Second jump, i.e. dodge.
        if self.timer >= self.FST_JUMP_DURATION + self.SND_JUMP_DELAY:
            drone.ctrl.jump = True
            drone.ctrl.pitch = -direction[0]
            drone.ctrl.paw = direction[1]

        # Expiration of the controller.
        if self.timer >= self.FST_JUMP_DURATION + self.SND_JUMP_DELAY + self.SND_JUMP_DURATION:
            drone.controller = None

        super().run(hive)


# TODO
# -> Half-flips
# -> Diagonal dodging -- https://www.youtube.com/watch?v=pX950bhGhJE
# -> PID Controller
# -> Aerial Turn
# -> Aerials (High / Low)
# -> Powershots
# -> Ball carry
# -> Flicks
# -> Drifts



#######
'''
    def snake(self, distance):
        """Makes the drones go in a line towards the ball"""

        # First drone follows the ball.
        target_speed = np.linalg.norm(self.ball.vel) + np.linalg.norm(self.ball.pos - self.drones[0].pos)/1.5
        go_to_point(self.drones[0], self.ball.pos, target_speed)

        # Create a tail behind the first drone.
        target = self.drones[0].pos - normalise(self.drones[0].vel) * distance
        self.tail = [target]

        for i, drone in enumerate(self.drones[1:]):
            target_speed = np.linalg.norm(self.drones[i].vel) + np.linalg.norm(self.drones[i].pos - self.drones[i+1].pos)/1.5
            go_to_point(drone, target, target_speed)
            target -= normalise(drone.vel) * distance
            self.tail.append(target)




def go_to_point(drone, point, target_speed):
    """Simple controller that takes the bot to a point.
    
    Arguments:
        drone {Drone} -- The drone being controlled.
        point {np.ndarray} -- World coordinates of the target point.
    """

    # Calculates location of point in local coordinates.
    local_point = local(drone.orient_m, drone.pos, point)

    # Finds 2D angle to point.
    # Positive is clockwise.
    angle = np.arctan2(local_point[1], local_point[0])

    def f(x, a):
        """Modified sigmoid"""
        # Graph: https://www.geogebra.org/m/udfp2zcy
        return 2 / (1 + np.exp(a*x)) - 1

    # Calculates steer.
    drone.ctrl.steer = f(angle, -3)
    
    # Calculates throttle.
    if np.linalg.norm(drone.vel) < target_speed:
        drone.ctrl.throttle = 1.0
    else:
        drone.ctrl.throttle = 0.0
'''