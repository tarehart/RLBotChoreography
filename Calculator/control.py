'''Controllers.'''

from rlbot.agents.base_agent import SimpleControllerState
import numpy as np
from utils import a3l, normalise, cap, local, special_sauce


class Controller:
    """Base controller class. Is inherited from by other controllers."""
    def __init__(self):
        self.timer = 0.0

    def run(self, agent):
        """Runs the controller
        
        Arguments:
            agent {BaseAgent} -- The agent.
        """
        # Increments timer.
        self.timer += agent.dt


class AngleBased(Controller):
    """Very basic controller which drives towards the target.

    Inheritance:
        Controller -- Base controller class. Is inherited from by other controllers.
    
    Behaviour:
        Throttle is always set to 1.
        Steers using a modified sigmoid function.
        Boosts when angle to target is below a certain threshold.
        Drifts if the angle to target is too large.

    Attributes:
        BOOST_ANGLE {float} -- Boosting angle threshold.
        DRIFT_ANGLE {float} -- Angle beyond which it will use handbrake.
    """
    def __init__(self):
        super().__init__()
        self.BOOST_ANGLE = 0.3
        self.DRIFT_ANGLE = 1.8

    def run(self, agent, player, target):
        """Runs the controller.
        
        Arguments:
            agent {BaseAgent} -- The agent.
            player {Car} -- Car object for which to generate controls.
            target {np.ndarray} -- World coordinates of the point to drive towards.
        """
        # Calculates angle to target.
        local_target = local(player.orient_m, player.pos, target)
        angle = np.arctan2(local_target[1], local_target[0])

        # Creates controller inputs.
        agent.ctrl.steer = special_sauce(angle, -5)

        if abs(angle) < self.BOOST_ANGLE:
            agent.ctrl.boost = True

        if abs(angle) > self.DRIFT_ANGLE:
            agent.ctrl.handbrake = True

        agent.ctrl.throttle = 1

        #super().run(agent) # Not needed here since this does not require a timer.


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

    def run(self, agent, player, target):
        """Runs the controller.
        
        Arguments:
            agent {BaseAgent} -- The agent.
            player {Car} -- Car object for which to generate controls.
            target {np.ndarray} -- World coordinates of where we want to hit the ball.
        """
        # Calculate drone's distance to ball.
        distance = np.linalg.norm(agent.ball.pos - agent.pos)

        # Find directions based on where we want to hit the ball.
        direction_to_hit = normalise(target - agent.ball.pos)
        perpendicular_to_hit = np.cross(direction_to_hit, a3l([0,0,1]))

        # Calculating component lengths and multiplying with direction.
        perpendicular_component = perpendicular_to_hit * cap(np.dot(perpendicular_to_hit, agent.ball.pos), -distance * self.PERP_DIST_COEFF, distance * self.PERP_DIST_COEFF)
        in_direction_component = -direction_to_hit * distance * self.DIRECT_DIST_COEFF

        # Combine components to get a drive target.
        drive_target = agent.ball.pos + in_direction_component + perpendicular_component

        super().run(agent, player, drive_target)


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
    def __init__(self, target):
        super().__init__()
        self.FST_JUMP_DURATION = 0.1
        self.SND_JUMP_DELAY = 0.1
        self.SND_JUMP_DURATION = 1.5 - self.FST_JUMP_DURATION - self.SND_JUMP_DELAY
        
    def run(self, agent, player, target):
        """Runs the controller.
        
        Arguments:
            agent {BaseAgent} -- The agent.
            player {Car} -- Car object for which to generate controls.
            target {np.ndarray} -- World coordinates of where to dodge towards.
        """
        # Calculates local target and direction.
        local_target = local(player.orient_m, player.pos, target)
        direction = normalise(local_target)

        # First jump
        if self.timer <= self.FST_JUMP_DURATION:
            agent.ctrl.jump = True
        
        # Second jump, i.e. dodge.
        if self.timer >= self.FST_JUMP_DURATION + self.SND_JUMP_DELAY:
            agent.ctrl.jump = True
            agent.ctrl.pitch = -direction[0]
            agent.ctrl.paw = direction[1]

        # Expiration of the controller.
        if self.timer >= self.FST_JUMP_DURATION + self.SND_JUMP_DELAY + self.SND_JUMP_DURATION:
            agent.controller = None

        super().run(agent)




class Kickoff(Controller):
    """Kickoff controller.
    
    Inheritance:
        Controller -- Base controller class. Is inherited from by other controllers.

    Behaviour:
        ...

    Attributes:
        ...
    """
    class Type:
        DEFAULT = 'DEFAULT'

    def __init__(self, closest):
        super().__init__()
        self.DODGE_TIME = 0.3

        # TODO Use randomness to pick from different kickoffs.
        self.type = self.Type.DEFAULT
        #self.got_boost = False
         
    def run(self, agent, player):
        """Runs the controller.
        
        Arguments:
            agent {BaseAgent} -- The agent.
            player {Car} -- Car object for which to generate controls.
        """
        if self.type == self.Type.DEFAULT:
            # Calculates angle to target.
            local_target = local(player.orient_m, player.pos, agent.ball.pos)
            angle = np.arctan2(local_target[1], local_target[0])

        agent.ctrl.steer = special_sauce(angle, -5)
        agent.ctrl.throttle = 1
        agent.ctrl.boost = 1

        ETA = np.linalg.norm(agent.ball.pos - player.pos) / np.linalg.norm(player.vel)

        if ETA <= self.DODGE_TIME:
            agent.controller = Dodge()

        super().run(agent)
