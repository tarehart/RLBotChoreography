"""Rendering for the Bot"""
#https://github.com/RLBot/RLBot/wiki/Rendering

"""
Palette:

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
from RLFunc     import a3l, world, gen_circle_points

def everything(s):
    """renders everything it can render"""
    debug(s)
    ctrl(s)
    turn_circles(s,20)

def debug(s):
    """prints debug info"""
    get_window_size(s)
    mw  = s.RLwindow[2] / 1000 #milliwidth
    mh  = s.RLwindow[3] / 1000 #milliheight

    s.renderer.begin_rendering('debug')

    #colours
    title   = s.renderer.team_color(team=None, alt_color=False)
    label   = s.renderer.white()
    val     = s.renderer.pink()

    #rendering
    loc     = [600*mw, 250*mh*s.calc_index]

        #title
    s.renderer.draw_string_2d(loc[0], loc[1], 2, 2, 'Calculator debug ' + str(s.calc_index), title)

        #box
    loc[1] += 40
    height  = 150 * mh
    width   = 180 * mw
    box     = [loc, [loc[0],loc[1]+height], [loc[0]+width,loc[1]+height], [loc[0]+width,loc[1]], loc]
    s.renderer.draw_polyline_2d(box, title)

        #text
    line1   = ('index: ',       str(s.index))
    line2   = ('player pos: ',  str((int(s.player.pos[0]),int(s.player.pos[1]),int(s.player.pos[2]))))
    line3   = ('turn radius: ', str(s.player.turn_r)[:10])

    loc     = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[0], label)
    loc     = [loc[0]+90*mw,loc[1]]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[1], val)

    s.renderer.end_rendering()

def ctrl(s):
    """prints controller input"""
    get_window_size(s)
    mw  = s.RLwindow[2] / 1000 #milliwidth
    mh  = s.RLwindow[3] / 1000 #milliheight

    s.renderer.begin_rendering('ctrl')

    #colours
    title   = s.renderer.team_color(team=None, alt_color=False)
    label   = s.renderer.white()
    val     = s.renderer.pink()

    #rendering
    loc     = [800*mw, 250*mh*s.calc_index]

        #title
    s.renderer.draw_string_2d(loc[0], loc[1], 2, 2, 'Controller input ' + str(s.calc_index), title)

        #box
    loc[1] += 40
    height  = 150 * mh
    width   = 180 * mw
    box     = [loc, [loc[0],loc[1]+height], [loc[0]+width,loc[1]+height], [loc[0]+width,loc[1]], loc]
    s.renderer.draw_polyline_2d(box, title)

        #text
    line1   = ('throttle: ',    str(s.ctrl.throttle))
    line2   = ('boost: ',       str(s.ctrl.boost))
    line3   = ('steer: ',       str(s.ctrl.steer))
    line4   = ('handbrake: ',   str(s.ctrl.handbrake))

    loc     = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+45, 1, 1, line4[0], label)
    loc     = [loc[0]+90*mw,loc[1]]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+45, 1, 1, line4[1], val)

    s.renderer.end_rendering()

def turn_circles(s,n):
    """renders turn circles"""
    r = s.player.turn_r
    A = s.player.A

    centreR = s.player.pos+world(a3l([0,r,0]),A)
    circleR = gen_circle_points(r,centreR,A,n)

    centreL = s.player.pos+world(a3l([0,-r,0]),A)
    circleL = gen_circle_points(r,centreL,A,n)

    s.renderer.begin_rendering("turn circles")

    #colours
    right   = s.renderer.red()
    left    = s.renderer.cyan()

    #rendering
    s.renderer.draw_polyline_3d(circleR, right)
    s.renderer.draw_polyline_3d(circleL, left)

    s.renderer.end_rendering()
    