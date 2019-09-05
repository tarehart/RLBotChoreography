'''States and controllers.'''

from rlbot.agents.base_agent import SimpleControllerState

from utils import np, local, normalise, cap, special_sauce

# -----------------------------------------------------------

# STATES:

class BaseState:
    def __init__(self):
        self.expired = False

    @staticmethod
    def available(agent):
        return True

    def execute(self, agent):
        if not agent.r_active:
            self.expired = True


class Idle(BaseState):
    def execute(self, agent):
        self.expired = True


class Kickoff(BaseState):
    def __init__(self):
        super().__init__()
        self.kickoff_pos = None

    @staticmethod
    def available(agent):
        return agent.ko_pause and agent.r_active

    def execute(self, agent):
        # If the kickoff pause ended and the ball has been touched recently, expire.
        if (not agent.ko_pause) and (agent.ball.last_touch.time_seconds + 0.1 > agent.game_time):
            self.expired = True

        agent.ctrl = simple(agent, agent.ball.pos)

        # TODO Do proper kickoff code.


class Catch(BaseState):

    def __init__(self):
        super().__init__()
        self.target_pos = None
        self.target_time = None
    
    @staticmethod
    def available(agent):
        bounces, times = Catch.get_bounces(agent)
        if len(bounces) > 0:
            # If there are some bounces, calculate the distance to them.
            vectors = bounces - agent.player.pos
            distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
                
            # Check if the bounces are reachable (rough estimate).
            good_time = distances/1000 + 0.5 <= times
            return np.count_nonzero(good_time) > 0

        else:
            return False
        
    def execute(self, agent):
        super().execute(agent)

        # Checks if the ball has been hit recently.
        if agent.ball.last_touch.time_seconds + 0.1 > agent.game_time:
            self.expired = True
        
        # Looks for bounce target.
        elif self.target_time is None:
            bounces, times = Catch.get_bounces(agent)

            if len(bounces) == 0:
                self.expired = True

            else:
                # Calculate the distance and estimate the time required to get there.
                vectors = bounces - agent.player.pos
                distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
                good_time = distances/1000 + 0.5<= np.squeeze(times)
            
                # Select the first good position and time.
                self.target_pos = bounces[good_time][0]
                self.target_time = times[good_time][0]

        # Expires state if too late.
        elif self.target_time < agent.game_time:
            self.expired = True

        # Else control to the target position.
        else:
            agent.ctrl = precise(agent, self.target_pos, self.target_time)

            # Draw a cyan square over the target position.
            agent.renderer.begin_rendering('Catch target')
            agent.renderer.draw_rect_3d(self.target_pos,10,10,True,agent.renderer.cyan())
            agent.renderer.end_rendering()


    @staticmethod
    def get_bounces(agent):
        # Looks for bounces in the ball predicion.
        z_pos = agent.ball.predict.pos[:,2]
        z_vel = agent.ball.predict.vel[:,2]
        bounce_bool = (z_vel[:-1] - 1000 < z_vel[1:]) & (z_pos[:-1] < 93)
        bounces = agent.ball.predict.pos[:-1][bounce_bool]
        times = agent.ball.predict.time[:-1][bounce_bool]
        return bounces, times


class DribbleToGoal(BaseState):
    pass


# -----------------------------------------------------------

# CONTROLLERS:

def simple(agent, target, ctrl = SimpleControllerState()):
    # Calculates angle to target.
    local_target = local(agent.player.orient_m, agent.player.pos, target)
    angle = np.arctan2(local_target[1], local_target[0])

    # Steer using special sauce.
    ctrl.steer = special_sauce(angle, -5)

    # Throttle always 1.
    ctrl.throttle = 1

    # Handbrake if large angle.
    if abs(angle) > 1.85:
        ctrl.handbrake = True

    # Boost if small angle.
    elif abs(angle) < 0.5:
        ctrl.boost = 1

    return ctrl


def precise(agent, target, time, ctrl = SimpleControllerState()):
    # Calculates angle to target.
    local_target = local(agent.player.orient_m, agent.player.pos, target)
    angle = np.arctan2(local_target[1], local_target[0])

    # Steer using special sauce.
    ctrl.steer = special_sauce(angle, -5)

    # Calculates the velocity in the direction of the ball and the desired velocity.
    towards_target = target - agent.player.pos
    distance = np.linalg.norm(towards_target)
    vel = np.dot(towards_target / distance, agent.player.vel)
    desired_vel = distance / (time - agent.game_time)

    # If the angle is small, use a speed controller.
    if abs(angle) <= 0.3:
        ctrl.throttle, ctrl.boost = speed_controller(vel, desired_vel, agent.dt)
        ctrl.handbrake = False

    # If the angle is too large, drift.
    elif abs(angle) >= 1.65:
        ctrl.throttle = 1
        ctrl.boost = False
        ctrl.handbrake = True

    # Else just try to do better. I know it's hard.
    else:
        ctrl.throttle = 0.5
        ctrl.boost = False
        ctrl.handbrake = False

    return ctrl


def speed_controller(current_vel, desired_vel, dt):
    """Returns the throttle and boost to get to desired velocity.
    
    Arguments:
        current_vel {float} -- The current forward velocity.
        desired_vel {float} -- Desired forward velocity.
        dt {float} -- Delta time for frame.
    
    Returns:
        float -- The throttle amount.
        bool -- Whether to boost or not.
    """
    desired_vel = cap(desired_vel, 0, 2300)

    # Gets the maximum acceleration based on current velocity.
    if current_vel < 0:
        possible_accel = 3500
    elif current_vel < 1400:
        possible_accel = (-36/35)*current_vel + 1600
    elif current_vel < 1410:
        possible_accel = -16*current_vel + 22560
    else:
        possible_accel = 0

    # Finds the desired change in velocity and 
    # the desired acceleration for the next tick.
    dv = desired_vel - current_vel
    desired_accel = dv / dt

    # If you want to slow down more than coast decceleration, brake.
    if desired_accel < -525 -800: # -525 is the coast deccel. Some extra to prevent it from spamming brake.
        throttle = -1
        boost = False

    # If you want to slow down a little bit, just coast.
    elif desired_accel < 0:
        throttle = 0
        boost = False

    # If you can accelerate just using your throttle, use proportions.
    elif possible_accel >= desired_accel:
        throttle = desired_accel / possible_accel
        boost = False

    # If you want to accelerate more, but less than the minimum you can do with boost (plus a little extra), just drive.
    elif desired_accel < (possible_accel + 991.667)*3 + 1000:
        throttle = 1
        boost = False

    # If you're really in a hurry, boost.
    else:
        throttle = 1
        boost = True

    return throttle, boost