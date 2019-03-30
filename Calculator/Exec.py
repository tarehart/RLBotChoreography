"""Control Input from Actions"""

def actions(s):
    """executes actions"""
    #test
    s.ctrl.throttle = 1.0

    #TODO toggle between human control and bot. Usable for only bot with calculator index 0?
    return s.ctrl