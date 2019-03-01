import math
import random
import time

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.quick_chats import QuickChats

from RLUtilities.Maneuvers import Drive, AirDodge
from RLUtilities.GameInfo import GameInfo
from RLUtilities.Simulation import Car, Ball, Input
from RLUtilities.LinearAlgebra import vec2, vec3, normalize, norm, dot

import Render

import win32gui

def kickoff(self):
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

    if self.kickoff_pos == None:
        car = self.info.my_car.pos
        self.kickoff_pos = pos_B_straight
        for pos in kickoff_positions:
            if norm(car - vec3(pos[0],pos[1],pos[2])) < norm(car - vec3(self.kickoff_pos[0],self.kickoff_pos[1],self.kickoff_pos[2])):
                self.kickoff_pos = pos

    if self.kickoff_pos == pos_B_straight or self.kickoff_pos == pos_O_straight:
        if self.timer == 0:
            print("straight")
        elif 0.5 <= self.timer < 0.7:
            self.controls.steer = 0.7
        elif 0.7 <= self.timer < 1.0:
            if self.action == None:
                car     = self.info.my_car
                direc   = dot(car.theta,vec3(500,-1000,0))
                target  = car.pos + direc
                self.action = AirDodge(car, 0.15, target)
            else:
                self.action.step(0.01666)
                self.controls = self.action.controls

        elif 1.6 <= self.timer < 1.8:
            self.action         = None
            self.controls.yaw   = -1.0

        elif 1.8 <= self.timer < 2.3:
            self.controls.steer   = -0.3

        elif 2.3 <= self.timer < 3.0:
            if self.action == None:
                car     = self.info.my_car
                target  = self.info.ball.pos
                self.action = AirDodge(car, 0.15, target)
                self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Reactions_Calculated)
            else:
                self.action.step(0.01666)
                self.controls = self.action.controls

        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0


    elif self.kickoff_pos == pos_B_backL or self.kickoff_pos == pos_O_backL:
        if self.timer == 0:
            print("backL")
        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0
        self.controls.steer     = -1.0


    elif self.kickoff_pos == pos_B_backR or self.kickoff_pos == pos_O_backR:
        if self.timer == 0:
            print("backR")
        self.controls.throttle  = 1.0
        self.controls.boost     = 1.0
        self.controls.steer     = 1.0


    elif self.kickoff_pos == pos_B_diagonalL or self.kickoff_pos == pos_O_diagonalL:
        if self.timer == 0:
            print("diagonalL")
        pass


    elif self.kickoff_pos == pos_B_diagonalR or self.kickoff_pos == pos_O_diagonalR:
        if self.timer == 0:
            print("diagonalR")
        pass


    else:
        if self.timer == 0:
            print("else")
        pass


    self.timer += self.dt


class Calculator(BaseAgent):
    def __init__(self, name, team, index):
        self.index          = index
        self.info           = GameInfo(index, team)
        self.controls       = SimpleControllerState()
        self.action         = None

        self.last_time      = 0.0
        self.dt             = 1.0 / 120.0

        self.timer          = 0.0
        self.kickoff_pos    = None
        self.state          = None


    def get_output(self, packet):
        self.info.read_packet(packet)

        #additional processing not done by RLU
        self.kickoff_pause  = packet.game_info.is_kickoff_pause
        self.dt             = self.info.time - self.last_time
        self.last_time      = self.info.time

        self.controls = SimpleControllerState()

        if self.state == None and self.kickoff_pause:
            self.kickoff_pos    = None
            self.timer          = 0.0
            self.state          = "kickoff"

        if self.state == "kickoff":
            kickoff(self)

            if self.timer >= 3.0:
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

        return self.controls