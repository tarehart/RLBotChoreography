'''For thinking and planning.'''

from utils import *

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
        
        # End this strategy if ball has moved and the kickoff pause has ended.
        if not s.ko_pause and np.any(s.ball.pos[:2] != np.array([0,0])):
            print("Oh no.")
            s.strategy = None

    elif s.strategy == Strategy.DEFENCE:

        # End this strategy if ball goes on their side.
        if s.ball.pos[1]*sign(s.team) > 0 or s.ko_pause:
            s.strategy = None

    elif s.strategy == Strategy.OFFENCE:

        # End this strategy if ball goes on our side.
        if s.ball.pos[1]*sign(s.team) < 0 or s.ko_pause:
            s.strategy = None




    # Pick a strategy
    else:

        # KICKOFF: At start of kickoff.
        if s.r_active and s.ko_pause:
            s.logger.info("KICKOFF")
            s.strategy = Strategy.KICKOFF

            for drone in s.drones:
                drone.kickoff = 'r_corner'
                print("index: {}".format(drone.index))
                for ko_pos in ko_positions:
                    dist_to_old_ko = abs(np.sum(drone.pos - ko_positions[drone.kickoff]*sign(s.team)))
                    dist_to_new_ko = abs(np.sum(drone.pos - ko_positions[ko_pos]*sign(s.team)))
                    if dist_to_new_ko < dist_to_old_ko:
                        drone.kickoff = ko_pos

                print(drone.kickoff)

                # Assigns a role to each bot for the kickoff.
                if drone.kickoff == 'r_corner' or drone.kickoff == 'l_corner':
                    if not any(d.role == Role.FORWARD for d in s.drones):
                        drone.role = Role.FORWARD
                    else:
                        drone.role = Role.DEFENDER
                elif drone.kickoff == 'r_back' or drone.kickoff == 'l_back':
                    if not any(d.role == Role.FORWARD for d in s.drones):
                        drone.role = Role.FORWARD
                    elif not any(d.role == Role.GOALIE for d in s.drones):
                        drone.role = Role.GOALIE
                    else:
                        drone.role = Role.DEFENDER
                else: #kickoff == 'centre'
                    if not any(d.role == Role.FORWARD for d in s.drones):
                        drone.role = Role.FORWARD
                    else:
                        drone.role = Role.GOALIE
            
        
        # DEFENCE: When the ball is on our half.
        elif s.ball.pos[1]*sign(s.team) < 0:
            s.logger.info("DEFENCE")
            s.strategy = Strategy.DEFENCE

        # OFFENCE: When the ball in on their half.
        elif s.ball.pos[1]*sign(s.team) > 0:
            s.logger.info("OFFENCE")
            s.strategy = Strategy.OFFENCE