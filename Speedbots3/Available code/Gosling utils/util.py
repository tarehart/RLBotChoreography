from objects import Vector3
import math

BEST_180_SPEED = 1000

def aerial(agent, target, time):
    #takes the agent, an intercept point, and an intercept time.Adjusts the agent's controller
    #(agent.c) to perform an aerial
    before = agent.c.jump
    dv_target = backsolve(target,agent,time)
    dv_total = dv_target.magnitude()
    dv_local = agent.me.matrix.dot(dv_target)
    angles = defaultPD(agent,dv_local)

    precision = cap((dv_total/1500),0.05, 0.60)

    if dv_local[2] > 100  or agent.me.airborne == False:
        if agent.sinceJump < 0.3:
            agent.c.jump = True
        elif agent.sinceJump >= 0.32:
            agent.c.jump = True
            agent.c.pitch = agent.c.yaw = agent.c.roll = 0
        else:
            agent.c.jump = False
    else:
        agent.c.jump = False

    if dv_total > 75:
        if abs(angles[1])+abs(angles[2]) < precision:
            agent.c.boost = True
        else:
            agent.c.boost = False
    else:
        fly_target = agent.me.matrix.dot(target - agent.me.location)
        angles = defaultPD(agent,fly_target)
        agent.c.boost = False
    
    
def backsolve(target,agent,time):
    #determines the delta-v required to reach a target on time
    d = target-agent.me.location

    dx = (2* ((d[0]/time)-agent.me.velocity[0]))/time
    dy = (2* ((d[1]/time)-agent.me.velocity[1]))/time
    dz = (2 * ((325*time)+((d[2]/time)-agent.me.velocity[2])))/time
    return Vector3(dx,dy,dz)

def cap(x, low, high):
    #caps/clamps a number between a low and high point
    if x < low:
        return low
    elif x > high:
        return high
    else:
        return x

def defaultPD(agent, local, direction = 0):
    #turns car to face a given local coordinate.
    #direction can specify left/right only turns w/ -1/1
    turn = math.atan2(local[1],local[0])
    turn = (math.pi * direction) + turn if direction != 0 else turn
    up =  agent.me.matrix.dot(Vector3(0,0,agent.me.location[2]))
    temp = [math.atan2(up[1],up[2]), math.atan2(local[2],local[0]), turn]
    target = temp#retargetPD(agent.me.rvel, temp)
    agent.c.steer = steerPD(turn, 0)
    agent.c.yaw = steerPD(target[2],-agent.me.rvel[2]/4)
    agent.c.pitch = steerPD(target[1],agent.me.rvel[1]/4)
    agent.c.roll = steerPD(target[0],agent.me.rvel[0]/2.5)
    return temp

def flip(agent,c,local):
    #dodges towards a local coordinate
    pitch = -sign(local[0])
    if not agent.me.airborn:
        c.jump = True
        agent.sinceJump = 0
    if agent.sinceJump <= 0.05:
        c.jump = True
        c.pitch = pitch
    elif agent.sinceJump > 0.05 and agent.sinceJump <= 0.1:
        c.jump = False
        c.pitch = pitch
    elif agent.sinceJump > 0.1 and agent.sinceJump <= 0.13:
        c.jump = True
        c.pitch = pitch
        c.roll = 0
        c.yaw = 0

def radius(v):
    #returns turn radius given velocity
    return 139.059 + (0.1539 * v) + (0.0001267716565 * v * v)

def side(x):
    #changes agent.team from 0,1 to -1,1
    if x <= 0:
        return -1
    return 1

def sign(x):
    #returns the sign of a number
    if x < 0:
        return -1
    elif x == 0:
        return 0
    else:
        return 1

def steerPD(angle,rate):
    #baby PD loop that takes an angle to turn and the current rate of turn
    final = ((35*(angle+rate))**3)/10
    return cap(final,-1,1)

def defaultThrottle(agent,target_speed,agent_speed,direction=1):
    #throttles towards a requested velocity. direction can be set to -1 for reverse
    final = ((abs(target_speed) - abs(agent_speed))/100) * direction
    if final > 1.5 or (final >0 and target_speed > 1410):
        agent.c.boost = True
    else:
        agent.c.boost = False
    if final > 0 and target_speed > 1410:
        final = 1
    agent.c.throttle= cap(final,-1,1)
