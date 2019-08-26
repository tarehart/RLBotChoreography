"""Control Input from Actions"""

from rlbot.agents.human.controller_input import controller

def actions(s):
    """executes actions"""
    if not s.human:
        #test
        s.ctrl.throttle = 1.0
    
    else:
        s.ctrl = controller.get_output()

    #TODO toggle between human control and bot. Usable for only bot with calculator index 0?
    return s.ctrl