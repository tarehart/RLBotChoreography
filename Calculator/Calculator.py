from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.quick_chats import QuickChats

from RLUtilities.Maneuvers import Drive, AirDodge, AerialTurn
from RLUtilities.GameInfo import GameInfo
from RLUtilities.Simulation import Car, Ball, Input
from RLUtilities.LinearAlgebra import vec3, norm, dot

import Render
import Kickoff

import math
import win32gui

class Calculator(BaseAgent):
    def __init__(self, name, team, index):
        self.index          = index
        self.info           = GameInfo(index, team)
        self.controls       = SimpleControllerState()
        self.action         = None

        self.last_time      = 0.0
        self.dt             = 1.0 / 120.0

        self.goals          = 0

        self.timer          = 0.0
        self.kickoff_pos    = None
        self.state          = None
        self.target         = None
        self.target_speed   = 2300

        #bot parameters
        self.target_range   = 200
        self.low_boost      = 25
        self.max_ball_dist  = 3000
        self.def_extra_dist = 500
        self.turn_c_quality = 20
        self.min_target_s   = 1000
        self.dodge_dist     = 200


    def get_output(self, packet):
        self.info.read_packet(packet)

        #additional processing not done by RLU
        self.kickoff_pause  = packet.game_info.is_kickoff_pause
        self.round_active   = packet.game_info.is_round_active
        self.dt             = self.info.time - self.last_time
        self.last_time      = self.info.time
        self.last_touch     = packet.game_ball.latest_touch.player_name
        
        #trashtalk
        if packet.game_cars[self.index].score_info.goals == self.goals + 1:
            self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Reactions_Calculated)
            
        self.goals          = packet.game_cars[self.index].score_info.goals

        #resets controls each tick
        self.controls = SimpleControllerState()

        #choose state
        if not self.round_active:
            self.state = None
        elif not self.state == "kickoff":
            if self.kickoff_pause:
                self.kickoff_pos    = None
                self.action         = None
                self.timer          = 0.0
                self.state          = "kickoff"
        
            elif not self.info.my_car.on_ground and not isinstance(self.action, AirDodge):
                self.state          = "recovery"
                self.action         = self.action = AerialTurn(self.info.my_car)

            elif norm(self.info.my_goal.center - self.info.my_car.pos) > norm(self.info.my_goal.center - self.info.ball.pos) + self.def_extra_dist:
                self.action         = None
                self.target_speed   = 2300
                self.state          = "defence"

                sign = 1 if self.team == 0 else -1
                self.target = vec3(0,sign*4000,0)

            elif self.info.my_car.pos[1] > 5120 or self.info.my_car.pos[1] < -5120:
                self.target         = vec3(0,5000,0) if self.info.my_car.pos[1] > 5120 else vec3(0,-5000,0)
                self.action         = self.action = Drive(self.info.my_car,self.target,1000)
                self.state          = "goal escape"

            elif self.state == None:
                self.action         = None
                self.target         = None
                self.target_speed   = 2300
                self.state          = "offence"


        #kickoff state
        if self.state == "kickoff":
            Kickoff.kickoff(self)

            #exit kickoff state
            if self.timer >= 2.6 or self.last_touch != '':
                self.state  = None
                self.action = None

        #recovery state
        elif self.state == "recovery":
            self.action.step(self.dt)
            self.controls           = self.action.controls
            self.controls.throttle  = 1.0
            
            #exit recovery state
            if self.info.my_car.on_ground == True:
                self.state  = None
                self.action = None


        #defence state and offence state
        elif self.state == "defence" or self.state == "offence":  
            #select target
            if self.target == None:
                #large boost
                if self.info.my_car.boost <= self.low_boost and norm(self.info.my_car.pos - self.info.ball.pos) > self.max_ball_dist:
                    active_pads = []
                    for pad in self.info.boost_pads:
                        if pad.is_active:
                            active_pads.append(pad)

                    if len(active_pads) != 0:
                        closest_pad = active_pads[0]
                        for pad in active_pads:
                            if norm(pad.pos - self.info.ball.pos) < norm(closest_pad.pos - self.info.ball.pos):
                                closest_pad = pad
                        self.target = closest_pad.pos
                    else:
                        self.target = self.info.ball.pos

                #ball        
                else:
                    self.target = self.info.ball.pos

            angle_to_target = math.atan2(dot(self.target, self.info.my_car.theta)[1], -dot(self.target, self.info.my_car.theta)[0])

            #select maneuver
            if not isinstance(self.action, AirDodge):
                if (-math.pi/4.0) <= angle_to_target <= (math.pi/4.0):
                    self.action = AirDodge(self.info.my_car,0.2,self.target)
                    self.timer  = 0.0
                else:
                    self.action = Drive(self.info.my_car,self.target,self.target_speed)
                
            #exit AirDodge
            else:
                self.timer += self.dt
                if self.timer >= 0.5:
                    self.action = None
            
            #maneuver tick
            if self.action != None:
                self.action.step(self.dt)
                self.controls   = self.action.controls
 
            #Drive
            if isinstance(self.action, Drive):
                #handbrake
                if (-math.pi/2.0) >= angle_to_target >= (math.pi/2.0):
                    self.controls.handbrake = True

                #target speed 
                else:
                    speed = norm(self.info.my_car.vel)
                    r = -6.901E-11 * speed**4 + 2.1815E-07 * speed**3 - 5.4437E-06 * speed**2 + 0.12496671 * speed + 157

                    if (norm(self.target - (self.info.my_car.pos + dot(self.info.my_car.theta,vec3(0,r,0)))) < r or norm(self.target - (self.info.my_car.pos + dot(self.info.my_car.theta,vec3(0,-r,0)))) < r) and not self.target_speed < self.min_target_s:
                        self.target_speed += -50
                        self.action = Drive(self.info.my_car,self.target,self.target_speed)
                    elif self.target_speed < 2300:
                        self.target_speed += 50
                        self.action = Drive(self.info.my_car,self.target,self.target_speed)

            #exit either state
            if (self.state == "defence" and norm(self.info.my_goal.center - self.info.my_car.pos) < norm(self.info.my_goal.center - self.info.ball.pos)) or (norm(self.target - self.info.my_car.pos) < self.target_range):
                self.state = None


        #goal escape state
        if self.state == "goal escape":
            self.action.step(self.dt)
            self.controls   = self.action.controls

            #exit goal escape state
            if not (self.info.my_car.pos[1] > 5120 or self.info.my_car.pos[1] < -5120):
                self.state  = None
                self.action = None


        #finding the size of the Rocket League window
        def callback(hwnd, win_rect):
            if "Rocket League" in win32gui.GetWindowText(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                win_rect[0] = rect[0]
                win_rect[1] = rect[1]
                win_rect[2] = rect[2] - rect[0]
                win_rect[3] = rect[3] - rect[1]

        self.RLwindow = [0] * 4
        win32gui.EnumWindows(callback, self.RLwindow)

        #Rendering
        Render.debug(self)
        Render.turn_circles(self)
        if not self.target == None:
            Render.target(self)

        return self.controls