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

from RLwindow import get_window_size

def all(s):
    """renders everything it can render"""
    debug(s)
    ctrl(s)

def debug(s):
    """prints debug info"""
    get_window_size(s)

    s.renderer.begin_rendering('debug')
    #colours
    title = s.renderer.team_color(team=None, alt_color=False)
    text = s.renderer.white()
    #rendering
    loc = [s.RLwindow[2]*0.6, (s.RLwindow[3]/4) * s.calc_index]
    s.renderer.draw_string_2d(loc[0], loc[1], 2, 2, 'Calculator debug ' + str(s.calc_index), title)

    loc[1] += 40
    box = [loc,[loc[0],loc[1]+120],[loc[0]+240,loc[1]+120],[loc[0]+240,loc[1]],loc]
    s.renderer.draw_polyline_2d(box, title)

    loc = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'index: ' + str(s.index), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'round active: ' + str(s.r_active), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'kickoff pause: ' + str(s.ko_pause), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'match ended: ' + str(s.m_ended), text)
    #loc[1] += 15
    s.renderer.end_rendering()

def ctrl(s):
    """prints controller input"""
    get_window_size(s)

    s.renderer.begin_rendering('ctrl')
    #colours
    title = s.renderer.team_color(team=None, alt_color=False)
    text = s.renderer.white()

    #rendering
    loc = [s.RLwindow[2]*0.8, (s.RLwindow[3]/4) * s.calc_index]
    s.renderer.draw_string_2d(loc[0], loc[1], 2, 2, 'Controller input ' + str(s.calc_index), title)

    loc[1] += 40
    box = [loc,[loc[0],loc[1]+120],[loc[0]+240,loc[1]+120],[loc[0]+240,loc[1]],loc]
    s.renderer.draw_polyline_2d(box, title)

    loc = [loc[0]+5,loc[1]+5]
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'throttle: ' + str(s.ctrl.throttle), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'boost: ' + str(s.ctrl.boost), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'steer ' + str(s.ctrl.steer), text)
    loc[1] += 15
    s.renderer.draw_string_2d(loc[0], loc[1], 1, 1, 'handbrake: ' + str(s.ctrl.handbrake), text)
    #loc[1] += 15
    s.renderer.end_rendering()

def circle(s,color,name,circle):
    s.renderer.begin_rendering(name)
    #s.renderer.draw_polyline_3d(locations, color)
    s.renderer.end_rendering()
