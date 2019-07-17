'''For handling strategy and planning.'''

import numpy as np
from utils import a3l, team_sign

from control import AB_control

# -----------------------------------------------------------

# STRATEGIES:

class Strategy:
    KICKOFF = 0
    DEFENCE = 1
    OFFENCE = 2

# TODO Think of better strategies; some fun ideas below:
# Idea: One drone carries ball, others try to demo opponent goalies.
# Idea: All drones turtle in goal except one who attacks the ball.
# Idea: Play as one large car in formation.
# Idea: Bots on each wing, passing from side to side.

# -----------------------------------------------------------

# ROLES:

class Demo():
    def __init__(self):
        self.name = "Demo"

    @staticmethod
    def execute(s, drone):
        pass

class Attacker():
    def __init__(self):
        self.name = "Attacker"
    
    @staticmethod
    def execute(s, drone):
        if s.strategy == Strategy.KICKOFF:
            AB_control(s, drone, s.ball.pos)

        else: #for testing
            AB_control(s, drone, s.ball.pos)

class Defender():
    def __init__(self):
        self.name = "Defender"

    @staticmethod
    def execute(s, drone):
        pass

class Goalie():
    def __init__(self):
        self.name = "Goalie"

    @staticmethod
    def execute(s, drone):
        pass

# -----------------------------------------------------------

# KICKOFF POSITIONS:

# Possible kickoff positions.
ko_positions = {
    'r_corner': a3l([-1952, -2464, 0]),
    'l_corner': a3l([ 1952, -2464, 0]),
    'r_back':   a3l([ -256, -3840, 0]),
    'l_back':   a3l([  256, -3840, 0]),
    'centre':   a3l([    0, -4608, 0])
}

# Positions in order of which should take the kickoff.
attacker_positions = [
    'r_corner',
    'l_corner',
    'r_back',
    'l_back',
    'centre'
]

# Positions in order of which should be a goalie.
goalie_positions = [
    'centre',
    'l_back',
    'r_back'
]

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
                # Resets roles.
                drone.role = None

                # Looks for closest match in kickoff positions.
                drone.kickoff = 'r_corner'
                for ko_pos in ko_positions:
                    if np.linalg.norm(drone.pos - ko_positions[ko_pos]*team_sign(s.team)) < 100:
                        drone.kickoff = ko_pos
                        break
                    #dist_to_old_ko = abs(np.sum(drone.pos - ko_positions[drone.kickoff]*team_sign(s.team)))
                    #dist_to_new_ko = abs(np.sum(drone.pos - ko_positions[ko_pos]*team_sign(s.team)))
                    #if dist_to_new_ko < dist_to_old_ko:
                    #    drone.kickoff = ko_pos

                print("Drone index {} on kickoff {} position.".format(drone.index, drone.kickoff))

            # Assigning Attacker role, i.e. who takes the kickoff.
            for pos in attacker_positions:
                for drone in s.drones:
                    if drone.kickoff == pos:
                        print('Attacker is drone {} in {} position.'.format(drone.index,drone.kickoff))
                        drone.role = Attacker()
                        break
                if any(isinstance(d.role, Attacker) for d in s.drones):
                    break

            # Assigning Defender role, takes boost in the kickoff.
            for pos in goalie_positions:
                for drone in s.drones:
                    if drone.kickoff == pos:
                            drone.role = Goalie()
                            break
                if any(isinstance(d.role, Goalie) for d in s.drones):
                    break
                        

            # The rest are assigned as Defenders.
            for drone in s.drones:
                if drone.role == None:
                    drone.role = Defender()
            
        
        #TODO Find better definitions for OFFENCE and DEFENCE

        # DEFENCE: When the ball is on our half.
        elif s.ball.pos[1]*team_sign(s.team) < 0:
            s.logger.info("DEFENCE START")
            s.strategy = Strategy.DEFENCE

        # OFFENCE: When the ball in on their half.
        elif s.ball.pos[1]*team_sign(s.team) > 0:
            s.logger.info("OFFENCE START")
            s.strategy = Strategy.OFFENCE