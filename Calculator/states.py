'''States and controllers.'''

from rlbot.agents.base_agent import SimpleControllerState

from utils import np, a3l, local, world, angle_between_vectors, normalise, cap, team_sign, special_sauce

orange_inside_goal = a3l([0, 5150, 0])

kickoff_positions = np.array([
    [-1952, -2464, 0], # r_corner
    [ 1952, -2464, 0], # l_corner
    [ -256, -3840, 0], # r_back
    [  256, -3840, 0], # l_back
    [  0.0, -4608, 0]  # centre
])

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

        if self.kickoff_pos is None:
            # Find closest kickoff position.
            vectors = kickoff_positions * team_sign(agent.team) - agent.player.pos
            distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
            self.kickoff_pos = np.where(distances == np.amin(distances))[0][0]

        distance = np.linalg.norm(agent.ball.pos - agent.player.pos)
        ETA = distance / np.linalg.norm(agent.player.vel)

        if ETA < 0.4:
            self.expired = True
            agent.state = Dodge(agent.ball.pos)

        # Go for small boost pad on back kickoffs.
        if self.kickoff_pos in (2,3) and distance > 3200:
            target = a3l([0, -2816, 70]) * team_sign(agent.team)
        else:
            target = agent.ball.pos

        agent.ctrl = simple(agent, target)

        super().execute(agent)

        # TODO Do proper kickoff code.



class Catch(BaseState):

    # TODO Directed catch if in front of goal to bounce it in.

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

                self.target_pos = bounce + direction*30
                self.target_time = times[good_time][0]

                if bounce[0] * team_sign(agent.team) > 4000:
                    self.target_pos[0] += 50 * normalise(bounce - orange_inside_goal*team_sign(agent.team))
                

        # Expires state if too late.
        elif self.target_time < agent.game_time:
            self.expired = True

        # Else control to the target position.
        else:
            agent.ctrl = precise(agent, self.target_pos, self.target_time)

            # Rendering.
            agent.renderer.begin_rendering('State')
            agent.renderer.draw_rect_3d(self.target_pos, 10, 10, True, agent.renderer.cyan())
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



class PickUp(BaseState):
    
    def __init__(self):
        super().__init__()
        self.ready_to_cut = False

    @staticmethod
    def available(agent):
        # Based on ball prediction and current position.
        small_z_vel = np.abs(agent.ball.predict.vel[:,2]) < 10
        predicted_roll = agent.ball.predict.pos[:,2] < 100
        on_ground = agent.ball.pos[2] < 100 and np.count_nonzero(small_z_vel & predicted_roll) > 60

        # Calculates some angles to determine where to place the offset.
        opponent_goal = orange_inside_goal * team_sign(agent.team)
        distance_to_goal = np.linalg.norm(agent.ball.pos - opponent_goal)
        distance_to_ball = np.linalg.norm(agent.ball.pos - agent.player.pos )
        good_distance = distance_to_goal > 4000 and distance_to_ball < 1000

        return on_ground and good_distance

    def execute(self, agent):

        # Checks if the ball has been hit recently.
        if agent.ball.last_touch.time_seconds + 0.1 > agent.game_time:
            self.expired = True
        if agent.ball.pos[2] > 100:
            self.expired = True

        if self.ready_to_cut:
            target = agent.ball.pos

        else:
            opponent_goal = orange_inside_goal * team_sign(agent.team)

            # Find components in direction and perpendicular to the ball velocity.
            ball_vel_direction = normalise(agent.ball.vel)
            perpendicular_to_vel = np.cross(ball_vel_direction, a3l([0,0,1]))

            # Calculating component lengths and multiplying with direction.
            perpendicular_component =  120 * perpendicular_to_vel * np.sign(np.dot(perpendicular_to_vel, agent.ball.pos - opponent_goal))

            # Combine components to get a drive target.
            target = agent.ball.pos + agent.ball.vel/20 + perpendicular_component

            if np.linalg.norm(target - agent.player.pos) < 80:
                self.ready_to_cut = True

        agent.ctrl = simple(agent, target)
        agent.ctrl.throttle, agent.ctrl.boost = speed_controller(np.linalg.norm(agent.player.vel), np.linalg.norm(agent.ball.vel) + 400, agent.dt)

        # Rendering.
        agent.renderer.begin_rendering('State')
        agent.renderer.draw_rect_3d(target, 10, 10, True, agent.renderer.cyan())
        agent.renderer.end_rendering()

        super().execute(agent)




class Dribble(BaseState):

    @staticmethod
    def available(agent):
        return agent.ball.pos[2] > 100 and np.linalg.norm(agent.ball.pos - agent.player.pos) < 300

    def execute(self, agent):

        # If ball touching ground, expire.
        if agent.ball.pos[2] < 100:
            self.expired = True
        if np.linalg.norm(agent.ball.pos - agent.player.pos) > 300:
            self.expired = True

        # Look into ball prediction for ball touching the ground.
        bool_array = agent.ball.predict.pos[:,2] < 100
        time = agent.ball.predict.time[bool_array][0]
        bounce = agent.ball.predict.pos[bool_array][0] * a3l([1,1,0])

        # Calculates some angles to determine where to place the offset.
        opponent_goal = orange_inside_goal * team_sign(agent.team)
        post_offset = 893 - 200

        l_post = opponent_goal + a3l([post_offset * team_sign(agent.team), 0, 0])
        r_post = opponent_goal - a3l([post_offset * team_sign(agent.team), 0, 0])
        ball_to_l_post = l_post - agent.ball.pos
        ball_to_r_post = r_post - agent.ball.pos

        # Angles measured clockwise starting from +x direction.
        l_post_angle = np.arctan2(ball_to_l_post[1], ball_to_l_post[0])
        r_post_angle = np.arctan2(ball_to_r_post[1], ball_to_r_post[0])

        # Special case for this so it works out nicely.
        ball_vel_angle = abs(np.arctan2(agent.ball.vel[1], agent.ball.vel[0])) * team_sign(agent.team)

        # Steer right is the angle is smaller than the left post.
        if ball_vel_angle < l_post_angle:
            angle_diff = l_post_angle - ball_vel_angle
            local_offset = a3l([-20, -30 * special_sauce(angle_diff, -10), 0])

        # Steer left if the angle is smaller than the right post.
        elif ball_vel_angle > r_post_angle:
            angle_diff = ball_vel_angle - r_post_angle
            local_offset = a3l([-20, 30 * special_sauce(angle_diff, -10), 0])

        # Else speed up forward.
        else:
            local_offset = a3l([-30, 0, 0])

        #if abs(angle) < goal_angle:
            #local_offset = a3l([-40, 0, 0])
        #else:
            #local_offset = a3l([-20, 25 * special_sauce(angle, 10) ,0])

        target = world(agent.player.orient_m, bounce, local_offset)

        # Drive to the target.
        agent.ctrl = precise(agent, target, time)

        #relative_ball = local(agent.player.orient_m, agent.player.pos, agent.ball.pos)
        #flick_sweetspot = a3l([40,0,135])
        #flick_distance = np.linalg.norm(flick_sweetspot - relative_ball)
        #goal_distance = np.linalg.norm(opponent_goal - agent.player.pos)
        
        # Flick if the angle is small and the distance is right.
        #if abs(angle) < 0.2 and flick_distance < 15 and (2000 < goal_distance < 5000):
        #    self.expired = True
        #    agent.state = Flick('BACKFLICK')

        # Rendering.
        agent.renderer.begin_rendering('State')
        agent.renderer.draw_rect_3d(target, 10, 10, True, agent.renderer.cyan())
        agent.renderer.draw_line_3d(agent.ball.pos, agent.ball.pos + agent.ball.vel, agent.renderer.red())
        agent.renderer.end_rendering()

        super().execute(agent)



class Flick(BaseState):
    def __init__(self, flick_type):
        super().__init__()
        self.flick_type = flick_type
        self.timer = 0.0
        
    def execute(self, agent):
        # TODO redo this in terms of relative positions and stuff.

        if self.flick_type == 'POP':
            pass


        elif self.flick_type == 'BACKFLICK':
            if self.timer < 0.1:
                pass
            elif self.timer < 0.3:
                agent.ctrl.jump = True
                agent.ctrl.yaw = 1
                agent.ctrl.pitch = 1
            
            elif self.timer < 0.5:
                agent.ctrl.boost = True
                agent.ctrl.yaw = 1

            elif self.timer < 1.1:
                agent.ctrl.yaw = 1

            elif self.timer < 1.2:
                agent.ctrl.jump = True
                agent.ctrl.pitch = 1
            else:
                self.expired = True
            
        agent.renderer.begin_rendering('State')
        agent.renderer.end_rendering()

        self.timer += agent.dt
        super().execute(agent)



class Dodge(BaseState):
    def __init__(self, target_pos):
        super().__init__()
        self.target_pos = target_pos
        self.timer = 0.0

    def execute(self, agent):
        if self.timer < 0.1:
            agent.ctrl.jump = True
        elif self.timer < 0.2:
            agent.ctrl.jump = False
            agent.ctrl.pitch = -0.5
        elif self.timer < 0.3:
            agent.ctrl.jump = True
            agent.ctrl.pitch = -1        
        else:
            self.expired = True

        agent.renderer.begin_rendering('State')
        agent.renderer.end_rendering()

        self.timer += agent.dt
        super().execute(agent)



class SimplePush(BaseState):

    def execute(self, agent):
        goal = orange_inside_goal * team_sign(agent.team) 

        # Calculate distance to ball.
        distance = np.linalg.norm(agent.ball.pos - agent.player.pos)

        # Find directions based on where we want to hit the ball.
        direction_to_hit = normalise(goal - agent.ball.pos)
        perpendicular_to_hit = np.cross(direction_to_hit, a3l([0,0,1]))

        # Calculating component lengths and multiplying with direction.
        perpendicular_component = perpendicular_to_hit * cap(np.dot(perpendicular_to_hit, agent.ball.pos), -distance/4, distance/4)
        in_direction_component = -direction_to_hit * distance/2

        # Combine components to get a drive target.
        target = agent.ball.pos + in_direction_component + perpendicular_component

        agent.ctrl = simple(agent, target)

        agent.renderer.begin_rendering('State')
        agent.renderer.draw_rect_3d(target, 10, 10, True, agent.renderer.cyan())
        agent.renderer.end_rendering()

        self.expired = True
        super().execute(agent)
        

class GetBoost(BaseState):
    @staticmethod
    def available(agent):
        if agent.player.boost < 30:
            ball_distance = np.linalg.norm(agent.ball.pos - agent.player.pos)
            for pad in agent.l_pads:
                if pad.active and np.linalg.norm(pad.pos - agent.player.pos) + 1000 < ball_distance:
                    return True
        return False

    def execute(self, agent):

        if agent.player.boost >= 80 or np.linalg.norm(agent.ball.pos - agent.player.pos) < 500:
            self.expired = True

        closest = agent.l_pads[0]
        for pad in agent.l_pads:
            if np.linalg.norm(pad.pos - agent.player.pos) < np.linalg.norm(closest.pos - agent.player.pos):
                closest = pad

        if not pad.active:
            self.expired = True

        agent.ctrl = simple(agent, pad.pos)
        super().execute(agent)



# -----------------------------------------------------------

# CONTROLLERS:

def simple(agent, target):
    # TODO Docstring
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
    elif abs(angle) < 0.3:
        ctrl.boost = True

    return ctrl


def precise(agent, target, time):
    # TODO Docstring
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
    time_remaining = time - agent.game_time
    if time_remaining == 0.0: return ctrl # 0 check so we don't divide by zero and break maths.
    desired_vel = distance / time_remaining

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
    if dt == 0.0: return 0.0, False

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
    if desired_accel < -525 -2000: # -525 is the coast deccel.
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
    elif desired_accel < (possible_accel + 991.667)*4:
        throttle = 1
        boost = False

    # If you're really in a hurry, boost.
    else:
        throttle = 1
        boost = True

    return throttle, boost