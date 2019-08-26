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
from RLFunc     import a3l, a3v, world, gen_circle_points

def everything(s):
    """renders everything it can render"""
    debug(s)
    ctrl(s)
    turn_circles(s,10)
    if s.calc_index == 0:
        ball_predict(s)
        ball(s,10)

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
    line2   = ('human ctrl: ',  str(s.human))
    line3   = ('player pos: ',  str((int(s.player.pos[0]),int(s.player.pos[1]),int(s.player.pos[2]))))
    line4   = ('turn radius: ', str(s.player.turn_r)[:10])
    #line5   = ('label: ',       str(value))
    #line6   = ('label: ',       str(value))

    loc     = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+45, 1, 1, line4[0], label)
    #s.renderer.draw_string_2d(loc[0], loc[1]+60, 1, 1, line5[0], label)
    #s.renderer.draw_string_2d(loc[0], loc[1]+75, 1, 1, line6[0], label)
    loc     = [loc[0]+90*mw,loc[1]]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+45, 1, 1, line4[1], val)
    #s.renderer.draw_string_2d(loc[0], loc[1]+60, 1, 1, line5[1], val)
    #s.renderer.draw_string_2d(loc[0], loc[1]+75, 1, 1, line6[1], val)

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
    #line5   = ('label: ',       str(value))
    #line6   = ('label: ',       str(value))

    loc     = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[0], label)
    s.renderer.draw_string_2d(loc[0], loc[1]+45, 1, 1, line4[0], label)
    #s.renderer.draw_string_2d(loc[0], loc[1]+60, 1, 1, line5[0], label)
    #s.renderer.draw_string_2d(loc[0], loc[1]+75, 1, 1, line6[0], label)
    loc     = [loc[0]+90*mw,loc[1]]
    s.renderer.draw_string_2d(loc[0], loc[1]   , 1, 1, line1[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+15, 1, 1, line2[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+30, 1, 1, line3[1], val)
    s.renderer.draw_string_2d(loc[0], loc[1]+45, 1, 1, line4[1], val)
    #s.renderer.draw_string_2d(loc[0], loc[1]+60, 1, 1, line5[1], val)
    #s.renderer.draw_string_2d(loc[0], loc[1]+75, 1, 1, line6[1], val)

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

def ball_predict(s):
    """renders the predicted path of the ball"""
    path = [a3v(pathslice.physics.location) for pathslice in s.ball.predict.slices[:-1]]

    s.renderer.begin_rendering("ball prediction")

    #colour
    pathcol = s.renderer.white()

    #rendering
    s.renderer.draw_polyline_3d(path, pathcol)

    s.renderer.end_rendering()


def ball(s,n):
    """renders three circles representing the ball"""
    ball = s.ball.pos
    r = 92.75
    XY = a3l([[1,0,0],[0,1,0],[0,0,1]])
    XZ = a3l([[0,0,1],[1,0,0],[0,1,0]])
    YZ = a3l([[0,1,0],[0,0,1],[1,0,0]])

    circleXY = gen_circle_points(r,ball,XY,n)
    circleXZ = gen_circle_points(r,ball,XZ,n)
    circleYZ = gen_circle_points(r,ball,YZ,n)

    s.renderer.begin_rendering("ball")

    #colours
    XYcol   = s.renderer.blue()
    XZcol   = s.renderer.lime()
    YZcol   = s.renderer.red()

    #rendering
    s.renderer.draw_polyline_3d(circleXY, XYcol)
    s.renderer.draw_polyline_3d(circleXZ, XZcol)
    s.renderer.draw_polyline_3d(circleYZ, YZcol)

    s.renderer.end_rendering()