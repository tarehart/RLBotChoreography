'''For handling state and planning.'''

from utils import np, a3l, team_sign
from control import Kickoff

# -----------------------------------------------------------

# STRATEGIES:

class State:
    KICKOFF = 'KICKOFF'
    DRIBBLE = 'DRIBBLE'
    DEMO = 'DEMO'


kickoff_positions = np.array([
    [-1952, -2464, 0], # r_corner
    [ 1952, -2464, 0], # l_corner
    [ -256, -3840, 0], # r_back
    [  256, -3840, 0], # l_back
    [  0.0, -4608, 0]  # centre
])


def states(self):

    
    if self.state == State.KICKOFF:
        


        # Exit condition: Pause ended and ball has moved.
        if not self.ko_pause and np.any(self.ball.pos[:2] != np.array([0,0])):
            self.state = None

    elif self.state == State.DRIBBLE:
        pass

    elif self.state == State.DEMO:
        pass

    else:
        # Choose state.

        # KICKOFF: At start of kickoff.
        if self.r_active and self.ko_pause:

            # Find closest kickoff position.
            vectors = kickoff_positions * team_sign(self.team) - self.player.pos
            distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
            closest = np.where(distances == np.amin(distances))[0][0]
            
            self.controller = Kickoff(closest)
            self.state = State.KICKOFF

        else:
            self.state = State.DRIBBLE