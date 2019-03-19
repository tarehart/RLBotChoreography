"""Rendering for the Bot"""
#https://github.com/RLBot/RLBot/wiki/Rendering

"""
Palette

s.renderer.black()
s.renderer.white()
s.renderer.black()
s.renderer.white()
s.renderer.gray()
s.renderer.blue()
s.renderer.red()
s.renderer.green()
s.renderer.lime()
s.renderer.yellow()
s.renderer.orange()
s.renderer.cyan()
s.renderer.pink()
s.renderer.purple()
s.renderer.teal()

s.renderer.team_color(team=None, alt_color=False)
s.renderer.create_color(a, r, g, b)
"""

from RLwindow   import get_window_size
from RLClasses  import Circle
from RLFunc     import a3l, world

def everything(s):
    """renders everything it can render"""
    debug(s)
    ctrl(s)
    turn_circles(s,20)

def debug(s):
    """prints debug info"""
    get_window_size(s)

    s.renderer.begin_rendering('debug')
    #colours
    title   = s.renderer.team_color(team=None, alt_color=False)
    text    = s.renderer.white()
    #rendering
    loc     = [s.RLwindow[2]*0.6, (s.RLwindow[3]/4) * s.calc_index]
    s.renderer.draw_string_2d(loc[0], loc[1], 2, 2, 'Calculator debug ' + str(s.calc_index), title)
        #box
    loc[1] += 40
    box     = [loc,[loc[0],loc[1]+120],[loc[0]+240,loc[1]+120],[loc[0]+240,loc[1]],loc]
    s.renderer.draw_polyline_2d(box, title)
        #text
    loc     = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'index: ' + str(s.index), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'turn radius: ' + str(s.player.turn_r), text)

    s.renderer.end_rendering()

def ctrl(s):
    """prints controller input"""
    get_window_size(s)

    s.renderer.begin_rendering('ctrl')
    #colours
    title   = s.renderer.team_color(team=None, alt_color=False)
    text    = s.renderer.white()

    #rendering
    loc     = [s.RLwindow[2]*0.8, (s.RLwindow[3]/4) * s.calc_index]
    s.renderer.draw_string_2d(loc[0], loc[1], 2, 2, 'Controller input ' + str(s.calc_index), title)
        #box
    loc[1] += 40
    box     = [loc,[loc[0],loc[1]+120],[loc[0]+240,loc[1]+120],[loc[0]+240,loc[1]],loc]
    s.renderer.draw_polyline_2d(box, title)
        #text
    loc     = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'throttle: ' + str(s.ctrl.throttle), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'boost: ' + str(s.ctrl.boost), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'steer ' + str(s.ctrl.steer), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'handbrake: ' + str(s.ctrl.handbrake), text)

    s.renderer.end_rendering()

def cyan_circle(s,name,circle,n):
    s.renderer.begin_rendering(name)
    #colour
    cyan = s.renderer.cyan()

    #rendering
    points = circle.generate_points(n)
    s.renderer.draw_polyline_3d(points, cyan)

    s.renderer.end_rendering()

def turn_circles(s,n):
    r = s.player.turn_r
    A = s.player.A

    centreR = s.player.pos+world(a3l([0,r,0]),A)
    circleR = Circle(r,centreR,A)
    cyan_circle(s,'circleR',circleR,n)

    centreL = s.player.pos+world(a3l([0,-r,0]),A)
    circleL = Circle(r,centreL,A)
    cyan_circle(s,'circleL',circleL,n)
