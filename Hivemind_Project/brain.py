from utils import *

class Strategy:
    KICKOFF = 0
    DEFENCE = 1
    OFFENCE = 2

def strat_plan(s):
    """Decides on strategy for the hivemind.
    
    Arguments:
        s {BotHelperProcess (self)} -- The hivemind.
    """

    if s.strategy == Strategy.KICKOFF:

        # End this strategy.
        if s.ball.last_t != "": #TODO Find a better way to detect if kickoff ended
            s.strategy = None

    elif s.strategy == Strategy.DEFENCE:

        # End this strategy.
        if s.ball.pos[1]*sign(s.team) > 0 or s.ko_pause:
            s.strategy = None

    elif s.strategy == Strategy.OFFENCE:

        # End this strategy.
        if s.ball.pos[1]*sign(s.team) <= 0 or s.ko_pause:
            s.strategy = None




    # Pick a strategy
    else:

        # KICKOFF: At start of kickoff.
        if s.r_active and s.ko_pause:
            s.logger.info("KICKOFF")
            s.strategy = Strategy.KICKOFF
        
        # DEFENCE: When the ball is on our half.
        elif s.ball.pos[1]*sign(s.team) < 0:
            s.logger.info("DEFENCE")
            s.strategy = Strategy.DEFENCE

        # OFFENCE: When the ball in on their half.
        elif s.ball.pos[1]*sign(s.team) >= 0:
            s.logger.info("OFFENCE")
            s.strategy = Strategy.OFFENCE