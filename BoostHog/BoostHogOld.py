import math
import random
#import time

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from RLUtilities.Maneuvers import Drive
from RLUtilities.GameInfo import GameInfo
from RLUtilities.Simulation import Car, Ball
from RLUtilities.LinearAlgebra import vec2, vec3, normalize, norm

from RLUtilities.controller_input import controller

class BoostHog(BaseAgent):

    def initialize_agent(self):
        self.info = GameInfo(self.index, self.team, self.get_field_info())
        self.controls = SimpleControllerState()
        self.phase = None
        self.targets = []
        self.guides = []
        self.active_pads = []
        self.plan_pads = []

    #plans a path using a bezier curve
    def pathplan(self):
        car = self.info.my_car
        k = 50 #number of guides on path
        p0_ = car.pos
        p1_ = car.pos + car.vel * 2 #compensation for velocity

        self.guides = []

        if len(self.targets) == 1:
            p2_ = self.targets[0]
        
            for i in range(k):
                self.guides.append(bezier(p0_,p1_,p2_,p2_,(i/k)))

        else:
            p2_ = self.targets[0]+normalize(self.targets[0]-self.targets[1])*100 #number not final, adjusts curve so that car ends up facing next target
            p3_ = self.targets[0]
            for i in range(k):
                self.guides.append(bezier(p0_,p1_,p2_,p3_,(i/k)))

    #find any convenient boost along path and adds it as a target
    def convboost(self):
        for guide in self.guides:
            for pad in self.active_pads:
                if pad not in self.plan_pads and norm(guide - pad.pos) <= 300: #number not final, distance from guide to potential convenient boost has to be less or equal to this number
                    self.plan_pads.append(pad)
                    self.targets.insert(0,pad.pos)
                    self.pathplan()
                    self.convboost()
                    break
            else:
                continue
            break

    def turn_radius(self):
        # https://docs.google.com/spreadsheets/d/1Hhg1TJqVUCcKIRmwvO2KHnRZG1z8K4Qn-UnAf5-Pt64/edit?usp=sharing
        car_speed = norm(self.info.my_car.vel)
        return (
            +156
            +0.1                * car_speed
            +0.000069           * car_speed**2
            +0.000000164        * car_speed**3
            -5.62*10**(-11)     * car_speed**4
        )   

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.info.read_packet(packet)
        
        if self.phase == None:
            self.phase = 1
        
        #phase 1: path-planning
        elif self.phase == 1:
            self.targets = [vec3(0,0,25)] #TODO pick targets
            
            self.pathplan()

            #adds all active boost pads to this list, big boosts first
            self.active_pads = []
            for pad in self.info.boost_pads:
                if pad.is_active:
                    self.active_pads.append(pad)
            for pad in self.info.small_boost_pads:
                if pad.is_active:
                    self.active_pads.append(pad)

            self.plan_pads = []
            self.convboost()
        
        #elif self.phase == 2:
            #TODO follow path

        #debug prints
        if True:
            self.renderer.begin_rendering("debug")
            self.renderer.draw_string_2d(20, 20, 1, 1, "phase: " + str(self.phase), self.renderer.black())
            self.renderer.draw_string_2d(20, 40, 1, 1, "targets: " + str(len(self.targets)), self.renderer.black())
            self.renderer.draw_string_2d(20, 60, 1, 1, "guides: " + str(len(self.guides)), self.renderer.black())
            self.renderer.draw_string_2d(20, 80, 1, 1, "big pads: " + str(len(self.info.boost_pads)), self.renderer.black())
            self.renderer.draw_string_2d(20, 100, 1, 1, "small pads: " + str(len(self.info.small_boost_pads)), self.renderer.black())
            self.renderer.draw_string_2d(20, 120, 1, 1, "active pads: " + str(len(self.active_pads)), self.renderer.black())
            self.renderer.draw_string_2d(20, 140, 1, 1, "turn radius: " + str(self.turn_radius()), self.renderer.black())
            self.renderer.draw_string_2d(20, 160, 1, 1, "car direction: " + "test", self.renderer.black())
            self.renderer.end_rendering()

        #renders targets
        for i in range(len(self.targets)):
            self.renderer.begin_rendering("target" + str(i))
            render_target(self,self.targets[i])
            self.renderer.end_rendering()

        #renders path
        self.renderer.begin_rendering("path")
        self.renderer.draw_polyline_3d(self.guides, self.renderer.white())
        self.renderer.end_rendering()

        return self.controls

#cubic bezier curve
def bezier(p0, p1, p2, p3, t):
    return ((1-t)**3)*p0 + 3*((1-t)**2)*t*p1 + 3*(1-t)*(t**2)*p2 + (t**3)*p3

#makes a blue cross about a point
def render_target(self,pos):
    self.renderer.draw_line_3d(pos - 100 * vec3(1, 0, 0), pos + 100 * vec3(1, 0, 0), self.renderer.blue())
    self.renderer.draw_line_3d(pos - 100 * vec3(0, 1, 0), pos + 100 * vec3(0, 1, 0), self.renderer.blue())
    self.renderer.draw_line_3d(pos - 100 * vec3(0, 0, 1), pos + 100 * vec3(0, 0, 1), self.renderer.blue())

#def render_circle(self, centre, radius):
    #points = []
    #tr = self.turn_radius()
    #for i in range(360):
        #get local of centre and then get locus of points
        #left = tr * cos(i)
        #forward = tr * sin(i)
        #points.append(i)
        