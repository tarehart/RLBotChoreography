'''For handling strategy and planning.'''

import numpy as np
from utils import a3l, team_sign, local
from control import AB_Control, GK_Control, LINE_PD_Control, Dodge

# -----------------------------------------------------------

# PARAMETERS:

KO_DODGE_TIME = 0.35
KO_PAD_TIME = 0.1

# -----------------------------------------------------------

# STRATEGIES:

class Strategy:
    KICKOFF = 0
    DEFENCE = 1
    OFFENCE = 2

# TODO Think of better strategies; some fun ideas below:
#   -> Take the ball and back-pass to allow Goalie to power shoot over everyone.
#   -> Team-pinches!
#   -> Demo attacks enemy Goalie while Attack dribbles ball to goal.
#   -> Shoot into corner, Support tries to hit on rebound.
#   -> Two Goalies, one on each side of goal.

# -----------------------------------------------------------

# ROLES:

# TODO Add functionality to each role.
# -> look at speedbots plan for inspiration.

class Demo():
    def __init__(self):
        self.name = "Demo"

    @staticmethod
    def execute(s, drone):

        # Steps through any mechanic the bot is attempting.
        if drone.controller is not None:
            drone.controller.run()


class Attacker:
    def __init__(self):
        self.name = "Attacker"
        self.timer = 0.0

    @staticmethod
    def execute(s, drone):
        drone.role.timer += s.dt

        if s.strategy == Strategy.KICKOFF:
            distance = np.linalg.norm(drone.pos - s.ball.pos)
            time_to_hit = distance / np.linalg.norm(drone.vel)

            if time_to_hit <= KO_DODGE_TIME:
                drone.controller = Dodge(drone, local(drone.orient_m, drone.pos, s.ball.pos))
                drone.role.timer = 0

            if drone.controller is None:
                if drone.kickoff == 'r_back' or drone.kickoff == 'l_back':
                    drone.controller = AB_Control(drone, a3l([0.0, -2816.0, 70.0])*team_sign(s.team))
                    drone.role.timer = 0
                    #drone.controller = LINE_PD_Control(drone, a3l([0,-6000,0])*team_sign(s.team), s.ball.pos)
                else:
                    drone.controller = AB_Control(drone, s.ball.pos)

            elif isinstance(drone.controller,AB_Control):
                if drone.role.timer >= KO_PAD_TIME:
                    AB_Control(drone, s.ball.pos)

        else:
            drone.controller = AB_Control(drone, s.ball.pos)


        if drone.controller is not None:
            if isinstance(drone.controller,Dodge):
                drone.controller.run(drone.role.timer)
            else: 
                drone.controller.run()


class Goalie:
    def __init__(self):
        self.name = "Goalie"

    @staticmethod
    def execute(s, drone):
        if s.strategy == Strategy.KICKOFF:
            if drone.controller is None:
                drone.controller = GK_Control(drone, goal_pos*team_sign(s.team))
    
        else:
            if drone.controller is None:
                drone.controller = GK_Control(drone, goal_pos*team_sign(s.team))

        if drone.controller is not None:
            drone.controller.run()


class Support:
    def __init__(self):
        self.name = "Support"

    @staticmethod
    def execute(s, drone):
        if s.strategy == Strategy.KICKOFF:
            if drone.controller is None:
                drone.controller = AB_Control(drone, best_boost[drone.kickoff]*team_sign(s.team))

        if drone.controller is not None:
            drone.controller.run()

# -----------------------------------------------------------

# KICKOFF POSITIONS:

kickoff_positions = {
    'r_corner' : a3l([-1952, -2464, 0]),
    'l_corner' : a3l([1952, -2464, 0]),
    'r_back' : a3l([-256.0, -3840, 0]),
    'l_back' : a3l([256.0, -3840, 0]),
    'centre' : a3l([0.0, -4608, 0])
}

goalie_positions = {
    'centre' : a3l([0.0, -4608, 0]),
    'r_back' : a3l([-256.0, -3840, 0]),
    'l_back' : a3l([256.0, -3840, 0])
}

best_boost = {
    'r_corner' : a3l([-3584.0, 0.0, 73.0]),
    'l_corner' : a3l([3584.0, 0.0, 73.0]),
    'r_back' : a3l([-3072.0, -4096.0, 73.0]),
    'l_back' : a3l([3072.0, -4096.0, 73.0])
}

goal_pos = a3l([0,-5300,0])

# -----------------------------------------------------------

# PLANNING:

def plan(s):
    """Decides on strategy for the hivemind and assigns drones to roles.
    
    Arguments:
        s {BotHelperProcess (self)} -- The hivemind.
    """

    if s.strategy == Strategy.KICKOFF:    

        # End this strategy if ball has moved and the kickoff pause has ended.
        if not s.ko_pause and np.any(s.ball.pos[:2] != np.array([0,0])):
            s.logger.info("KICKOFF END")
            s.strategy = None

    elif s.strategy == Strategy.DEFENCE:

        # End this strategy if ball goes on their side.
        if s.ball.pos[1]*team_sign(s.team) > 0 or s.ko_pause:
            s.logger.info("DEFENCE END")
            s.strategy = None

    elif s.strategy == Strategy.OFFENCE:

        # End this strategy if ball goes on our side.
        if s.ball.pos[1]*team_sign(s.team) < 0 or s.ko_pause:
            s.logger.info("OFFENCE END")
            s.strategy = None


    # Pick a strategy
    else:
        # KICKOFF: At start of kickoff.
        if s.r_active and s.ko_pause:
            s.logger.info("KICKOFF START")
            s.strategy = Strategy.KICKOFF

            # Finds drones' kickoff positions.
            for drone in s.drones:
                # Resets roles and controllers.
                drone.role = None
                drone.controller = None

                # Looks for closest match in kickoff positions.
                drone.kickoff = 'r_corner'
                for pos in kickoff_positions:
                    if np.linalg.norm(drone.pos - kickoff_positions[pos]*team_sign(s.team)) < 100:
                        drone.kickoff = pos
                        break

                print("Drone index {} on kickoff {} position.".format(drone.index, drone.kickoff))

            # Assigning Attacker role, i.e. who takes the kickoff.
            for pos in kickoff_positions:
                if any([isinstance(drone.role, Attacker) for drone in s.drones]):
                    break
                for drone in s.drones:
                    if drone.kickoff == pos and drone.role is None:
                        drone.role = Attacker()
                        break

            # Assigning Goalie role.
            for pos in goalie_positions:
                if any([isinstance(drone.role, Goalie) for drone in s.drones]):
                    break
                for drone in s.drones:
                    if drone.kickoff == pos and drone.role is None:
                        drone.role = Goalie()
                        break
            
            # The rest are assigned as Support.
            for drone in s.drones:
                if drone.role is None:
                    drone.role = Support()
                        
        
        # TODO Find better definitions for OFFENCE and DEFENCE
        # TODO Pick roles more intelligently.

        # DEFENCE: When the ball is on our half.
        elif s.ball.pos[1]*team_sign(s.team) < 0:
            s.logger.info("DEFENCE START")
            s.strategy = Strategy.DEFENCE

            # Assigns Goalie role to closest drone to goal.
            potential_goalie = s.drones[0]
            for drone in s.drones:
                # Resets roles and controllers.
                drone.role = None
                drone.controller = None

                # Checks if drone is closer to goal than the previous potential goalie.
                if np.linalg.norm(potential_goalie.pos - goal_pos*team_sign(s.team)) > np.linalg.norm(drone.pos - goal_pos*team_sign(s.team)):
                    potential_goalie = drone
            
            potential_goalie.role = Goalie()

            # The rest are assigned as Attacker.
            for drone in s.drones:
                if drone.role is None:
                    drone.role = Attacker()


        # OFFENCE: When the ball in on their half.
        elif s.ball.pos[1]*team_sign(s.team) > 0:
            s.logger.info("OFFENCE START")
            s.strategy = Strategy.OFFENCE

            # Assigns all drones to Attackers.
            for drone in s.drones:
                # Resets roles and controllers.
                drone.role = None
                drone.controller = None

                drone.role = Attacker()