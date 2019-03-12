from RLUtilities.Maneuvers import AirDodge, Drive
from RLUtilities.LinearAlgebra import vec3, norm, dot

def kickoff(self):
    """kickoff"""
    pos_B_straight  = [    0, -4608, 0]
    pos_B_backL     = [  256, -3840, 0]
    pos_B_backR     = [ -256, -3840, 0]
    pos_B_diagonalL = [ 1952, -2464, 0]
    pos_B_diagonalR = [-1952, -2464, 0]

    pos_O_straight  = [    0,  4608, 0]
    pos_O_backL     = [ -256,  3840, 0]
    pos_O_backR     = [  256,  3840, 0]
    pos_O_diagonalL = [-1952,  2464, 0]
    pos_O_diagonalR = [ 1952,  2464, 0]

    kickoff_positions = [
        pos_B_straight,
        pos_B_backL,
        pos_B_backR,
        pos_B_diagonalL,
        pos_B_diagonalR,

        pos_O_straight,
        pos_O_backL,
        pos_O_backR,
        pos_O_diagonalL,
        pos_O_diagonalR,
    ]

    car = self.info.my_car

    #identifies kickoff position
    if self.kickoff_pos == None:
        take_kickoff = True
        for mate in self.info.teammates:
            if norm(self.info.ball.pos - mate.pos) + 50 < norm(self.info.ball.pos - car.pos):
                take_kickoff = False 

        if take_kickoff == True:
            self.kickoff_pos = pos_B_straight
            for pos in kickoff_positions:
                if norm(car.pos - vec3(pos[0],pos[1],pos[2])) < norm(car.pos - vec3(self.kickoff_pos[0],self.kickoff_pos[1],self.kickoff_pos[2])):
                    self.kickoff_pos = pos
        else:
            self.kickoff_pos = None

    #straight kickoff
    if self.kickoff_pos == pos_B_straight or self.kickoff_pos == pos_O_straight:
        if self.timer == 0:
            print("straight")
        elif 0.5 <= self.timer < 0.7:
            self.controls.steer = 0.7
        elif 0.7 <= self.timer < 1.0:
            if self.action == None:
                direc   = dot(car.theta,vec3(500,-1000,0))
                target  = car.pos + direc
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls = self.action.controls
        elif 1.6 <= self.timer < 1.8:
            self.action         = None
            self.controls.yaw   = -1.0
        elif 1.8 <= self.timer < 2.3:
            self.controls.steer = -0.3
        """
        elif 2.35 <= self.timer < 2.6:
            if self.action == None:
                target  = self.info.ball.pos
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls = self.action.controls
        """

        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0

    #backL kickoff
    elif self.kickoff_pos == pos_B_backL or self.kickoff_pos == pos_O_backL:
        if self.timer == 0:
            print("backL")
        elif 0.1 <= self.timer < 0.4:
            self.controls.steer = 1.0
        elif 0.4 <= self.timer < 0.7:
            self.controls.steer = -0.5
        elif 0.7 <= self.timer < 1.5:
            if self.action == None:
                direc   = dot(car.theta,vec3(500,-2000,0))
                target  = car.pos + direc
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls   = self.action.controls
        elif 1.5 <= self.timer < 2.6:
            self.action         = None
            self.controls.steer = -1.0
        """
        elif 2.15 <= self.timer < 2.6:
            if self.action == None:
                target  = self.info.ball.pos
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls   = self.action.controls
        """

        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0

    #backR kickoff
    elif self.kickoff_pos == pos_B_backR or self.kickoff_pos == pos_O_backR:
        if self.timer == 0:
            print("backR")
        elif 0.1 <= self.timer < 0.4:
            self.controls.steer = -1.0
        elif 0.4 <= self.timer < 0.7:
            self.controls.steer = 0.5
        elif 0.7 <= self.timer < 1.5:
            if self.action == None:
                direc   = dot(car.theta,vec3(500,2000,0))
                target  = car.pos + direc
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls = self.action.controls
        elif 1.5 <= self.timer < 2.6:
            self.action         = None
            self.controls.steer = 1.0
        """
        elif 2.15 <= self.timer < 2.6:
            if self.action == None:
                target  = self.info.ball.pos
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls   = self.action.controls
        """

        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0

    #diagonalL kickoff
    elif self.kickoff_pos == pos_B_diagonalL or self.kickoff_pos == pos_O_diagonalL:
        if self.timer == 0:
            print("diagonalL")
        elif 0.1 <= self.timer < 0.3:
            self.controls.steer = -0.6
        elif 0.4 <= self.timer < 1.0:
            if self.action == None:
                direc   = dot(car.theta,vec3(500,1500,0))
                target  = car.pos + direc
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls = self.action.controls
        elif 1.0 <= self.timer < 1.9:
            self.action = None
            self.controls.steer = -0.8
        elif 1.9 <= self.timer < 2.6:
            if self.action == None:
                target  = self.info.ball.pos
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls   = self.action.controls

        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0

    #diagonalR kickoff
    elif self.kickoff_pos == pos_B_diagonalR or self.kickoff_pos == pos_O_diagonalR:
        if self.timer == 0:
            print("diagonalR")
        elif 0.1 <= self.timer < 0.3:
            self.controls.steer = 0.6
        elif 0.4 <= self.timer < 1.0:
            if self.action == None:
                direc   = dot(car.theta,vec3(500,-1500,0))
                target  = car.pos + direc
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls = self.action.controls
        elif 1.0 <= self.timer < 1.9:
            self.action = None
            self.controls.steer = 0.8
        elif 1.9 <= self.timer < 2.6:
            if self.action == None:
                target  = self.info.ball.pos
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(self.dt*2)
                self.controls   = self.action.controls

        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0

    #invalid kickoff
    else:
        if self.timer == 0.0:
            print("invalid or teammate kickoff")
            closest_pad = self.info.boost_pads[0]
            for pad in self.info.boost_pads:
                if norm(pad.pos - self.info.ball.pos) < norm(closest_pad.pos - self.info.ball.pos):
                    closest_pad = pad
            self.target = closest_pad.pos
        else:
            self.action = Drive(self.info.my_car,self.target,2300)
            self.action.step(self.dt)
            self.controls   = self.action.controls


    self.timer += self.dt
