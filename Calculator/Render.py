"""Rendering for the Bot"""

def all(s):
    """renders everything it can render"""
    debug(s)

def debug(s):
    """prints debug info"""
    s.renderer.begin_rendering("debug")
    s.renderer.draw_string_2d(20, 10, 2, 2, str(s.ctrl), s.renderer.red())
    s.renderer.end_rendering()