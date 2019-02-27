from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.quick_chats import QuickChats

import Data
import Plan
import Exec
import Render
from util import *

import win32gui

#Whiteboard: https://awwapp.com/b/usirwotjj/

class BoostHog(BaseAgent):
    def initialize_agent(self):
        Data.init(self)
        
        #parameters
        self.const_convboost = 300
        


    def get_output(self, packet):
        Data.process(self, packet)
        Plan.state(self)

        if self.state == "kickoff":
            Exec.kickoff(self)
            
        elif self.state == "plan":
            Plan.targets(self)

            self.plan_pads = []

            #self.send_quick_chat(QuickChats.CHAT_EVERYONE, QuickChats.Reactions_Calculated)

            self.state = "exec"

        elif self.state == "exec":
            Exec.path(self)

            if len(self.guides) < 4 or dist2d(self.player.pos, self.guides[0]) > 200.0:
                self.state = "plan"

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
        Render.path(self)
        Render.debug(self)
        Render.targets(self)
        Render.turn_circles(self)

        return self


