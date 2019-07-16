'''For handling strategy and planning.'''

import numpy as np
from utils import a3l, team_sign
from actions import Behaviour, Action

# Big picture strategy.
class Strategy:
    KICKOFF = 0
    DEFENCE = 1
    OFFENCE = 2

# Roles for specific drones. Will do different things depending on strategy.
class Role:
    ATBA = 0
    DEMO = 1
    FORWARD = 2
    MIDFIELD = 3
    DEFENDER = 4
    GOALIE = 5

# Possible kickoff positions.
ko_positions = {
    'r_corner': a3l([-1952, -2464, 0]),
    'l_corner': a3l([ 1952, -2464, 0]),
    'r_back':   a3l([ -256, -3840, 0]),
    'l_back':   a3l([  256, -3840, 0]),
    'centre':   a3l([    0, -4608, 0])
}

def plan(s):
    """Decides on strategy for the hivemind and assigns drones to tasks.
    
    Arguments:
        s {BotHelperProcess (self)} -- The hivemind.
    """

    if s.strategy == Strategy.KICKOFF:

        for drone in s.drones:
            if drone.role == Role.FORWARD:
                # Take the kickoff.
                drone.behaviour = Behaviour.FAST_TO_TARGET
                drone.target = s.ball.pos

            elif drone.role == Role.DEFENDER:
                # Go grab boost and prepare to follow up.
                drone.action = Behaviour.COLLECT_BOOST
                pass

            elif drone.role == Role.GOALIE:
                # Go to goal and watch out for shots.
                pass
        
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
                drone.kickoff = 'r_corner'
                print("index: {}".format(drone.index))
                for ko_pos in ko_positions:
                    dist_to_old_ko = abs(np.sum(drone.pos - ko_positions[drone.kickoff]*team_sign(s.team)))
                    dist_to_new_ko = abs(np.sum(drone.pos - ko_positions[ko_pos]*team_sign(s.team)))
                    if dist_to_new_ko < dist_to_old_ko:
                        drone.kickoff = ko_pos

                print(drone.kickoff)

                # Assigns a role to each bot for the kickoff.
                if drone.kickoff == 'r_corner' or drone.kickoff == 'l_corner':
                    # Take the kickoff if no one is taking yet, otherwise play as defender.
                    if not any(d.role == Role.FORWARD for d in s.drones):
                        drone.role = Role.FORWARD
                    else:
                        drone.role = Role.DEFENDER

                elif drone.kickoff == 'r_back' or drone.kickoff == 'l_back':
                    # Take the kickoff if no one is taking yet, otherwise play as goalie if no goalie yet, otherwise defend.
                    if not any(d.role == Role.FORWARD for d in s.drones):
                        drone.role = Role.FORWARD
                    elif not any(d.role == Role.GOALIE for d in s.drones):
                        drone.role = Role.GOALIE
                    else:
                        drone.role = Role.DEFENDER

                else: #kickoff == 'centre'
                    # Take the kickoff if no one else is taking yet, otherwise play as goalie. (Should only take kickoffs in 1v1.)
                    if not any(d.role == Role.FORWARD for d in s.drones):
                        drone.role = Role.FORWARD
                    else:
                        drone.role = Role.GOALIE
            
        
        #TODO Find better definitions for OFFENCE and DEFENCE

        # DEFENCE: When the ball is on our half.
        elif s.ball.pos[1]*team_sign(s.team) < 0:
            s.logger.info("DEFENCE START")
            s.strategy = Strategy.DEFENCE

        # OFFENCE: When the ball in on their half.
        elif s.ball.pos[1]*team_sign(s.team) > 0:
            s.logger.info("OFFENCE START")
            s.strategy = Strategy.OFFENCE