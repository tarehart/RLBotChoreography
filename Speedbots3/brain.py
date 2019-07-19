import numpy as np
from utils import a3l, team_sign, local
from control import AB_Control, GK_Control, LINE_PD_Control, Dodge


#PARAMETERS:

KO_DODGE_TIME = 0.35
KO_PAD_TIME = 0.1

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

class Strategy:
    KICKOFF = 0
    OFFENCE = 1
    DEFENCE = 2

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


def think(s):
    if s.strategy == Strategy.KICKOFF:
        # exit condition.
        if not s.ko_pause:
            print("KICKOFF END")
            s.strategy = None

    elif s.strategy == Strategy.DEFENCE:
        # exit condition.
        if s.ball.pos[1]*team_sign(s.team) > 0:
            print("DEFENCE END")
            s.strategy = None

    elif s.strategy == Strategy.OFFENCE:
        # exit condition.
        if s.ball.pos[1]*team_sign(s.team) < 0:
            print("OFFENCE END")
            s.strategy = None

    
    if s.strategy is None:

        # Kickoff.
        if s.r_active and s.ko_pause:
            print("KICKOFF START")
            s.strategy = Strategy.KICKOFF

            for drone in s.drones:
                drone.role = None
                drone.controller = None

                closest = 'r_corner'
                for pos in kickoff_positions:
                    current = np.linalg.norm(kickoff_positions[closest]*team_sign(s.team) - drone.pos)
                    new = np.linalg.norm(kickoff_positions[pos]*team_sign(s.team) - drone.pos)
                    if new < current:
                        closest = pos
                drone.kickoff = closest

            for pos in kickoff_positions:
                if any([isinstance(drone.role,Attacker) for drone in s.drones]):
                    break
                for drone in s.drones:
                    if drone.kickoff == pos and drone.role is None:
                        drone.role = Attacker()
                        break

            for pos in goalie_positions:
                if any([isinstance(drone.role,Goalie) for drone in s.drones]):
                    break
                for drone in s.drones:
                    if drone.kickoff == pos and drone.role is None:
                        drone.role = Goalie()
                        break
            
            for drone in s.drones:
                if drone.role is None:
                    drone.role = Support()

        # Defence.
        elif s.ball.pos[1]*team_sign(s.team) < 0:
            s.strategy = Strategy.DEFENCE
            print("DEFENCE START")

            potential_goalie = s.drones[0]
            for drone in s.drones:
                drone.role = None
                drone.controller = None
                if np.linalg.norm(potential_goalie.pos - goal_pos*team_sign(s.team)) > np.linalg.norm(drone.pos - goal_pos*team_sign(s.team)):
                    potential_goalie = drone
            
            potential_goalie.role = Goalie()

            for drone in s.drones:
                if drone.role is None:
                        drone.role = Attacker()

        # Offence.
        elif s.ball.pos[1]*team_sign(s.team) > 0:
            s.strategy = Strategy.OFFENCE
            print("OFFENCE START")

            for drone in s.drones:
                drone.role = None
                drone.controller = None

                drone.role = Attacker()
