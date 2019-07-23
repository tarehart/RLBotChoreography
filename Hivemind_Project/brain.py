'''For handling strategy and planning.'''

import numpy as np
from utils import a3l, team_sign, local
from control import AngleBased, TargetShot, Dodge

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
#   -> Demos surround opponent from multiple sides.

# -----------------------------------------------------------

# ROLES:

# TODO Add functionality to each role.
# -> look at speedbots plan for inspiration.

class Role:
    def __init__(self, name):
        self.name = name
        self.timer = 0.0

    def execute(self, hive, drone):
        self.timer += hive.dt
        # Steps through any mechanic the bot is attempting.
        if drone.controller is not None:
            drone.controller.run()

class Demo(Role):
    def __init__(self):
        super().__init__("Demo")

    @staticmethod
    def execute(self, hive, drone):
        if hive.strategy == Strategy.DEFENCE:
            if self.target is None:
                # Assign target as closest opponent to ball.
                self.target = sorted(hive.opponents, key=lambda car: np.linalg.norm(car.pos - hive.ball.pos))[0]

            if drone.controller is None:
                pass

        super().execute(hive, drone)

# TODO: Rewrite Roles to work with new controllers.
'''
class Attacker(Role):
    def __init__(self):
        super().__init__("Attacker")
        
    @staticmethod
    def execute(hive, drone):
        drone.role.timer += hive.dt

        if hive.strategy == Strategy.KICKOFF:
            distance = np.linalg.norm(drone.pos - hive.ball.pos)
            time_to_hit = distance / np.linalg.norm(drone.vel) if np.linalg.norm(drone.vel) > 0 else 10

            if time_to_hit <= KO_DODGE_TIME:
                drone.controller = Dodge(drone, local(drone.orient_m, drone.pos, hive.ball.pos))
                drone.role.timer = 0

            if drone.controller is None:
                if drone.kickoff == 'r_back' or drone.kickoff == 'l_back':
                    drone.controller = AB_Control(drone, a3l([0.0, -2816.0, 70.0])*team_sign(hive.team))
                    drone.role.timer = 0
                    #drone.controller = LINE_PD_Control(drone, a3l([0,-6000,0])*team_sign(hive.team), hive.ball.pos)
                else:
                    drone.controller = AB_Control(drone, hive.ball.pos)

            elif isinstance(drone.controller,AB_Control):
                if drone.role.timer >= KO_PAD_TIME:
                    AB_Control(drone, hive.ball.pos)

        else:
            drone.controller = AB_Control(drone, hive.ball.pos)


        if drone.controller is not None:
            if isinstance(drone.controller,Dodge):
                drone.controller.run(drone.role.timer)
            else: 
                drone.controller.run()


class Goalie(Role):
    def __init__(self):
        super().__init__("Goalie")

    @staticmethod
    def execute(s, drone):
        if hive.strategy == Strategy.KICKOFF:
            if drone.controller is None:
                drone.controller = GK_Control(drone, goal_pos*team_sign(hive.team))
    
        else:
            if drone.controller is None:
                drone.controller = GK_Control(drone, goal_pos*team_sign(hive.team))

        if drone.controller is not None:
            drone.controller.run()


class Support(Role):
    def __init__(self):
        super().__init__("Support")

    @staticmethod
    def execute(s, drone):
        if hive.strategy == Strategy.KICKOFF:
            if drone.controller is None:
                drone.controller = AB_Control(drone, best_boost[drone.kickoff]*team_sign(hive.team))

        if drone.controller is not None:
            drone.controller.run()
'''

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

# TODO Consider using lambda sorting for kickoffs or other?

# -----------------------------------------------------------

# PLANNING:

def plan(hive):
    """Decides on strategy for the hivemind and assigns drones to roles.
    
    Arguments:
        hive {BotHelperProcess (self)} -- The hivemind.
    """

    if hive.strategy == Strategy.KICKOFF:    

        # End this strategy if ball has moved and the kickoff pause has ended.
        if not hive.ko_pause and np.any(hive.ball.pos[:2] != np.array([0,0])):
            hive.logger.info("KICKOFF END")
            hive.strategy = None

    elif hive.strategy == Strategy.DEFENCE:

        # End this strategy if ball goes on their side.
        if hive.ball.pos[1]*team_sign(hive.team) > 0 or hive.ko_pause:
            hive.logger.info("DEFENCE END")
            hive.strategy = None

    elif hive.strategy == Strategy.OFFENCE:

        # End this strategy if ball goes on our side.
        if hive.ball.pos[1]*team_sign(hive.team) < 0 or hive.ko_pause:
            hive.logger.info("OFFENCE END")
            hive.strategy = None


    # Pick a strategy
    else:
        # KICKOFF: At start of kickoff.
        if hive.r_active and hive.ko_pause:
            hive.logger.info("KICKOFF START")
            hive.strategy = Strategy.KICKOFF

            # Finds drones' kickoff positions.
            for drone in hive.drones:
                # Resets roles and controllers.
                drone.role = None
                drone.controller = None

                # Looks for closest match in kickoff positions.
                drone.kickoff = 'r_corner'
                for pos in kickoff_positions:
                    if np.linalg.norm(drone.pos - kickoff_positions[pos]*team_sign(hive.team)) < 100:
                        drone.kickoff = pos
                        break

                print("Drone index {} on kickoff {} position.".format(drone.index, drone.kickoff))

            # Assigning Attacker role, i.e. who takes the kickoff.
            for pos in kickoff_positions:
                if any([isinstance(drone.role, Attacker) for drone in hive.drones]):
                    break
                for drone in hive.drones:
                    if drone.kickoff == pos and drone.role is None:
                        drone.role = Attacker()
                        break

            # Assigning Goalie role.
            for pos in goalie_positions:
                if any([isinstance(drone.role, Goalie) for drone in hive.drones]):
                    break
                for drone in hive.drones:
                    if drone.kickoff == pos and drone.role is None:
                        drone.role = Goalie()
                        break
            
            # The rest are assigned as Support.
            for drone in hive.drones:
                if drone.role is None:
                    drone.role = Support()
                        
        
        # TODO Find better definitions for OFFENCE and DEFENCE
        # TODO Pick roles more intelligently.

        # DEFENCE: When the ball is on our half.
        elif hive.ball.pos[1]*team_sign(hive.team) < 0:
            hive.logger.info("DEFENCE START")
            hive.strategy = Strategy.DEFENCE

            # Assigns Goalie role to closest drone to goal.
            potential_goalie = hive.drones[0]
            for drone in hive.drones:
                # Resets roles and controllers.
                drone.role = None
                drone.controller = None

                # Checks if drone is closer to goal than the previous potential goalie.
                if np.linalg.norm(potential_goalie.pos - goal_pos*team_sign(hive.team)) > np.linalg.norm(drone.pos - goal_pos*team_sign(hive.team)):
                    potential_goalie = drone
            
            potential_goalie.role = Goalie()

            # The rest are assigned as Attacker.
            for drone in hive.drones:
                if drone.role is None:
                    drone.role = Attacker()


        # OFFENCE: When the ball in on their half.
        elif hive.ball.pos[1]*team_sign(hive.team) > 0:
            hive.logger.info("OFFENCE START")
            hive.strategy = Strategy.OFFENCE

            # Assigns all drones to Attackers.
            for drone in hive.drones:
                # Resets roles and controllers.
                drone.role = None
                drone.controller = None
                drone.role = Attacker()