import numpy as np
from scipy.interpolate import interp1d
#import matplotlib.pyplot as plt

from utils import a3l, normalise

def straight(start, end, n):
    t = np.linspace(0,1,n)[:,np.newaxis]
    return t*start + (1-t)*end

def arc(centre, radius, start, end, n):
    theta = np.linspace(start, end, n)[:,np.newaxis]
    sin = np.sin(theta)
    cos = np.cos(theta)
    zero = np.zeros_like(sin)
    points = np.concatenate((cos, sin, zero), axis=1) * radius
    return centre + points

def bezier_cubic(p0, p1, p2, p3, n : int):
    p0 = p0
    p1 = p1
    p2 = p2
    p3 = p3
    t = np.linspace(0.0, 1.0, n)[:,np.newaxis]
    path = (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3
    return path

def test_path(detail):
    # Path definition.
    a = a3l([3072, -4096, 0])
    b = a3l([3072, 2300, 0])
    c = a3l([1072,2300,0])

    part1 = straight(a, b, detail)
    part2 = arc(c, 2000, 0, 3*np.pi/4, detail)

    d = part2[-1]
    e = d + 1500 * normalise(part2[-1] - part2[-2])
    f = a3l([0, 1024, 0])
    g = a3l([0, 0, 0])

    part3 = bezier_cubic(d, e, f, g, detail)

    h = a3l([-512, 0, 0])

    part4 = arc(h, 512, 0, -np.pi, detail)

    i = part4[-1]
    j = i + 1500 * normalise(part4[-1] - part4[-2])
    k = a3l([-2800, 1200, 0])
    l = a3l([-3500, 500, 0])

    part5 = bezier_cubic(i, j, k, l, detail)

    m = 2*l - k
    n = a3l([-3072, -1200, 0])
    o = a3l([-3072, -2000, 0])
    p = a3l([-3072, -4096, 0])

    part6 = bezier_cubic(l, m, n, o, detail)
    part7 = straight(o, p, detail)

    # Connect all the parts.
    path = np.concatenate((part1, part2, part3, part4, part5, part6, part7))

    return path
'''
def display_path(path):
    fig, ax = plt.subplots()
    img = plt.imread("field.png")
    ax.imshow(img, extent=[-4096, 4096, -5120, 5120])

    path *= a3l([-1, 1, 1])
    ax.plot(path[:,0], path[:,1], '-w')

    plt.show()
'''
def get_path_length(path):
    a = path[:-1]
    b = path[1:]
    diff = b - a
    return np.einsum('i->', np.sqrt(np.einsum('ij,ij->i',diff,diff)))

def reparam_by_arc_len(path):
    a = path[:-1]
    b = path[1:]
    diff = b - a
    lengths = np.sqrt(np.einsum('ij,ij->i',diff,diff))
    working_len = 0
    result = np.zeros(len(path))
    for i in range(len(path)-1):
        working_len += lengths[i]
        result[i+1] = working_len    
    return result

def get_curvature(path):
    dx_dt = np.gradient(path[:, 0])
    dy_dt = np.gradient(path[:, 1])

    d2x_dt2 = np.gradient(dx_dt)
    d2y_dt2 = np.gradient(dy_dt)

    curvature = np.abs(d2x_dt2 * dy_dt - dx_dt * d2y_dt2) / (dx_dt * dx_dt + dy_dt * dy_dt)**1.5    

    return curvature

def max_speed_from_curve(path_k):
    k = path_k.copy()
    s = np.array([0, 500, 1000, 1500, 1750, 2300])
    K = np.array([0.0069, 0.00396, 0.00235, 0.001375, 0.0011, 0.00088])
    f = interp1d(K, s)
    k[k<0.00088] = 0.00088
    k[k>0.0069] = 0.0069
    max_s = f(k)
    return max_s 

def path_analysis(path, start_vel = 0):
    path_curvature  = get_curvature(path)
    path_velocities = max_speed_from_curve(path_curvature)

    # Displacements
    a = path[:-1]
    b = path[1:]
    diff = b - a
    displacements = np.sqrt(np.einsum('ij,ij->i',diff,diff))

    # Forward pass.
    current_vel = start_vel # Initial velocity
    f_path_velocities = path_velocities.copy()
    f_path_velocities[0] = current_vel

    for i in range(len(f_path_velocities)-1):
        # Get max velocity from path.
        path_vel = path_velocities[i]
        
        # Homebrewed interpolation to get max acceleration
        if current_vel >= 1400:
            if current_vel >= 1410:
                possible_accel = 0
            else:
                possible_accel = -16*current_vel + 22560
        else:
            if current_vel >= 0:
                possible_accel = (-36/35)*current_vel + 1600
            else:
                possible_accel = 3500
        
        ### possible_accel += 991.667 # Assuming you have boost.

        # Get greatest possible velocity.
        possible_vel = np.sqrt(current_vel**2 + possible_accel*displacements[i])

        # Use the smaller of the two velocities.
        current_vel = possible_vel if possible_vel < path_vel else path_vel
        f_path_velocities[i+1] = current_vel

    # Backward pass.
    b_path_velocities = f_path_velocities.copy()
    b_path_velocities[0] = current_vel
    reversed_displacements = displacements[::-1]
    reversed_f_path_velocities = f_path_velocities[::-1]

    for i in range(len(f_path_velocities)-1):
        # Get the path velocity.
        path_vel = reversed_f_path_velocities[i]

        # Calculate maximum velocity.
        # We are going backwards through the velocities so this means braking.
        possible_vel = np.sqrt(current_vel**2 + 3500*reversed_displacements[i])

        # Use the smaller of the two velocities.
        current_vel = path_vel if path_vel <= possible_vel else possible_vel
        b_path_velocities[i+1] = current_vel

    # Reverse the backwards pass.
    b_path_velocities = b_path_velocities[::-1]

    # Getting time estimate.
    # Using einsum is faster although more obscure. 
    # It is basically just dividing displacements by velocities and then summing the times.
    time_estimate = np.einsum('i,i', displacements, 1/b_path_velocities[1:])

    return time_estimate, b_path_velocities


'''
# Pathing test.
ball_state = BallState(physics = Physics(location=Vector3(z=3000)))
car_state = {self.index: CarState(physics = Physics(location=Vector3(3072, -4100, 18), rotation=Rotator(0, np.pi/2, 0), velocity=Vector3(0, 0, 0)))}
game_state = GameState(ball = ball_state, cars = car_state)
self.set_game_state(game_state)

self.path = paths.test_path(10)
self.path_time, self.path_vels = paths.path_analysis(self.path, 0)
self.timer = 0.0
'''

'''
def follow_path(agent, path, path_velocities):
    # Create the controller state.
    ctrl = SimpleControllerState()

    # Find closest point in path.
    vectors = path - agent.pos
    distances = np.sqrt(np.einsum('ij,ij->i', vectors, vectors))
    closest = np.where(distances == np.amin(distances))[0][0]

    # Gets next point.
    next_point = path[closest+1]

    # Use predicted path velocities.
    if np.linalg.norm(agent.vel) <= path_velocities[closest+1]:
        ctrl.throttle = 1
    else:
        ctrl.throttle = -1

    # Calculates the target position in local coordinates.
    local_target = local(agent.orient_m, agent.pos, next_point)
    # Finds 2D angle to target. Positive is clockwise.
    angle = np.arctan2(local_target[1], local_target[0])

    ctrl.steer = special_sauce(angle, -3)
    
    return ctrl
'''