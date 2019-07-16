#from utils import 

# Behaviours are similar to what other people call states; they determine what kind of thing the bot should be doing.
class Behaviour:
    FAST_TO_TARGET = 0
    FRUGAL_TO_TARGET = 1
    COLLECT_BOOST = 2
    FOLLOW_PATH = 3

# Actions are special moves that the behaviours use.
class Action:
    DODGE = 0
    CARRY = 1

def run(s, drone):
    if drone.behaviour == Behaviour.FAST_TO_TARGET:
        return drone.ctrl
    else:
        return drone.ctrl

def AngleControl(drone, target):
    pass

def PDControl(drone, path):
    pass


#TODO Figure out how to do stuff.