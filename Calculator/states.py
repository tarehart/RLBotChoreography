'''States and controllers.'''

from rlbot.agents.base_agent import SimpleControllerState

from utils import np, a3l, local, world, angle_between_vectors, normalise, cap, team_sign, special_sauce

orange_inside_goal = a3l([0, 5150, 0])

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

        super().execute(agent)

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
            good_time = distances/1000 <= np.squeeze(times)
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
                good_time = distances/1000 <= np.squeeze(times)
            
                # Select the first good position and time.
                bounce = bounces[good_time][0] * a3l([1,1,0])
                direction = normalise(agent.player.pos * a3l([1,1,0]) - bounce)
                self.target_pos = bounce + direction*40
                self.target_time = times[good_time][0]

        # Expires state if too late.
        elif self.target_time < agent.game_time:
            self.expired = True

        # Else control to the target position.
        else:
            agent.ctrl = precise(agent, self.target_pos, self.target_time)

            # Draw a cyan square over the target position.
            agent.renderer.begin_rendering('State')
            agent.renderer.draw_rect_3d(self.target_pos, 10, 10, True, agent.renderer.cyan())
            agent.renderer.draw_polyline_3d((agent.ball.pos, self.target_pos, agent.player.pos), agent.renderer.white())
            agent.renderer.end_rendering()

        super().execute(agent)


    @staticmethod
    def get_bounces(agent):
        # Looks for bounces in the ball predicion.
        z_pos = agent.ball.predict.pos[:,2]
        z_vel = agent.ball.predict.vel[:,2]
        # Compares change in z velocity between ticks and whether the ball is on the ground.
        bounce_bool = (z_vel[:-1] < z_vel[1:] - 500) & (z_pos[:-1] < 100)
        bounces = agent.ball.predict.pos[:-1][bounce_bool]
        times = agent.ball.predict.time[:-1][bounce_bool]
        return bounces, times


class Dribble(BaseState):

    @staticmethod
    def available(agent):
        return agent.ball.pos[2] > 100 and np.linalg.norm(agent.ball.pos - agent.player.pos) < 300

    def execute(self, agent):

        # If ball touching ground, expire.
        if agent.ball.pos[2] < 100:
            self.expired = True

        # Look into ball prediction for ball touching the ground.
        bool_array = agent.ball.predict.pos[:,2] < 100
        time = agent.ball.predict.time[bool_array][0]
        bounce = agent.ball.predict.pos[bool_array][0] * a3l([1,1,0])

        # Calculates angle to opponent's goal
        opponent_goal = orange_inside_goal * team_sign(agent.team)
        ball_to_goal = opponent_goal - agent.ball.pos
        angle = angle_between_vectors(ball_to_goal, agent.ball.vel * a3l([1,1,0])) * np.sign(agent.ball.vel[0])

        # Create an offset to control the ball.
        distance = np.linalg.norm(opponent_goal - agent.player.pos)
        goal_angle = np.arctan2(892.775,distance)

        if abs(angle) < goal_angle:
            local_offset = a3l([-30, 0, 0])
        else:
            local_offset = a3l([-15,20*np.sign(-angle),0])

        offset = world(agent.player.orient_m, a3l([0,0,0]), local_offset)

        target = bounce + offset
        agent.ctrl = precise(agent, target, time)

        agent.renderer.begin_rendering('State')
        agent.renderer.draw_rect_3d(target, 10, 10, True, agent.renderer.cyan())
        agent.renderer.draw_polyline_3d((agent.ball.pos, target, agent.player.pos), agent.renderer.white())
        agent.renderer.end_rendering()
        
        super().execute(agent)


class Flick(BaseState):
    pass


class GetBoost(BaseState):
    @staticmethod
    def available(agent):
        return agent.player.boost < 30 and np.linalg.norm(agent.ball.pos - agent.player.pos) > 1000

    def execute(self, agent):

        if agent.player.boost >= 80 or np.linalg.norm(agent.ball.pos - agent.player.pos) < 500:
            self.expired = True

        closest = agent.l_pads[0]
        for pad in agent.l_pads:
            if np.linalg.norm(pad.pos - agent.player.pos) < np.linalg.norm(closest.pos - agent.player.pos):
                closest = pad

        agent.ctrl = simple(agent, pad.pos)

        super().execute(agent)



# -----------------------------------------------------------

# CONTROLLERS:

def simple(agent, target):

    ctrl = SimpleControllerState()

    # Calculates angle to target.
    local_target = local(agent.player.orient_m, agent.player.pos, target)
    angle = np.arctan2(local_target[1], local_target[0])

    # Steer using special sauce.
    ctrl.steer = special_sauce(angle, -5)

    # Throttle always 1.
    ctrl.throttle = 1

    # Handbrake if large angle.
    if abs(angle) > 1.65:
        ctrl.handbrake = True

    # Boost if small angle.
    elif abs(angle) < 0.5:
        ctrl.boost = 1

    return ctrl


def precise(agent, target, time):
    ctrl = SimpleControllerState()

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

    if distance < 50:
        ctrl.throttle = 0.0
        ctrl.boost = 0.0

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
    if dt > 0.0:
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
        if desired_accel < -525 -1000: # -525 is the coast deccel.
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

    else:
        return 1.0, False