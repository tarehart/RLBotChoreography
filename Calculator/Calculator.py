from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator
from rlbot.utils.structures.quick_chats import QuickChats

from RLUtilities.Maneuvers import Drive, AirDodge
from RLUtilities.GameInfo import GameInfo
from RLUtilities.Simulation import Car, Ball, Input
from RLUtilities.LinearAlgebra import vec2, vec3, normalize, norm, dot

import Render
import Kickoff

import win32gui

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
        self.round_active   = packet.game_info.is_round_active
        self.dt             = self.info.time - self.last_time
        self.last_time      = self.info.time
        self.last_touch     = packet.game_ball.latest_touch.player_name

        self.controls = SimpleControllerState()

        if not self.state == "kickoff" and self.kickoff_pause and self.round_active:
            self.kickoff_pos    = None
            self.timer          = 0.0
            self.action         = None
            self.state          = "kickoff"
        
        if self.state == None:
            self.state          = "normal"

        if self.state == "kickoff":
            Kickoff.kickoff(self)

            if self.timer >= 2.6 or self.last_touch != '':
                self.state  = None
                self.action = None
                self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Reactions_Calculated)

        if self.state == "normal":
            self.action     = Drive(self.info.my_car,self.info.ball.pos,2300)
            self.action.step(self.dt)
            self.controls   = self.action.controls

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