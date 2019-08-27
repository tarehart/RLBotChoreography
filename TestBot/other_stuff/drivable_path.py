import numpy as np
from scipy.interpolate import interp1d

def bezier_cubic(p0, p1, p2, p3, n : int):
    p0 = p0[:,np.newaxis]
    p1 = p1[:,np.newaxis]
    p2 = p2[:,np.newaxis]
    p3 = p3[:,np.newaxis]
    t = np.linspace(0.0, 1.0, n)
    path = (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3
    return path.T

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
        
        possible_accel += 991.667 # Assuming you have boost.

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

p0 = np.array([0,0,0])
p1 = np.array([100,-500,0])
p2 = np.array([400,-500,0])
p3 = np.array([1000,0,0])

n = 100

path = bezier_cubic(p0, p1, p2, p3, n)

path_analysis(path)

