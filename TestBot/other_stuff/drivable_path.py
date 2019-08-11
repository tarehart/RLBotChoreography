import numpy as np
import matplotlib.pyplot as plt
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

p0 = np.array([0,0,0])
p1 = np.array([100,-500,0])
p2 = np.array([400,-500,0])
p3 = np.array([1000,0,0])

n = 10000

path = bezier_cubic(p0, p1, p2, p3, n)
path_by_arc_len = reparam_by_arc_len(path)
path_curvature  = get_curvature(path)
path_velocities = max_speed_from_curve(path_curvature)

# Displacements
a = path[:-1]
b = path[1:]
diff = b - a
displacements = np.sqrt(np.einsum('ij,ij->i',diff,diff))

# Forward pass.
current_vel = 0 # Initial velocity
f_path_velocities = path_velocities.copy()
f_path_velocities[0] = current_vel

'''
v = np.array([0, 1400, 1410, 2300])
a = np.array([1600, 160, 0, 0])
f = interp1d(v, a)

for i in range(len(path_velocities)-1):
    path_vel = path_velocities[i]
    possible_accel = f(current_vel) + 991.667 # Assuming you have boost.
    possible_vel = np.sqrt(current_vel**2 + possible_accel*displacements[i])
    current_vel = possible_vel if possible_vel < path_vel else path_vel
    f_path_velocities[i+1] = current_vel
'''
for i in range(n-1):
    path_vel = path_velocities[i]
    
    # Homebrewed interpolation
    # m = (y2-y1) / (x2-x1)
    # c = y1 - m*x1
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
    possible_vel = np.sqrt(current_vel**2 + possible_accel*displacements[i])
    current_vel = possible_vel if possible_vel < path_vel else path_vel
    f_path_velocities[i+1] = current_vel

# Backward pass.
b_path_velocities = f_path_velocities.copy()
b_path_velocities[0] = current_vel
reversed_displacements = displacements[::-1]
reversed_f_path_velocities = f_path_velocities[::-1]
for i in range(len(f_path_velocities)-1):
    path_vel = reversed_f_path_velocities[i]
    possible_vel = np.sqrt(current_vel**2 + 3500*reversed_displacements[i])
    current_vel = path_vel if path_vel <= possible_vel else possible_vel
    b_path_velocities[i+1] = current_vel
b_path_velocities = b_path_velocities[::-1]


path_len = get_path_length(path)
print(f'total length: {path_len}')
time_estimate = np.einsum('i,i', displacements, 1/b_path_velocities[1:])
print(f'time estimate: {time_estimate}')

# Plotting
plt.rcParams['figure.figsize'] = [10, 20]

plt.subplot(5,1,1)
plt.plot(path[:,0], path[:,1])
plt.ylabel('Path')

plt.subplot(5,1,2)
plt.plot(path_by_arc_len, path_curvature)
plt.xlabel('Arc length')
plt.ylabel('Curvature')

plt.subplot(5,1,3)
plt.plot(path_by_arc_len, path_velocities)
plt.xlabel('Arc length')
plt.ylabel('Velocity')

plt.subplot(5,1,4)
plt.plot(path_by_arc_len, f_path_velocities)
plt.xlabel('Arc length')
plt.ylabel('Velocity after f-pass')

plt.subplot(5,1,5)
plt.plot(path_by_arc_len, b_path_velocities)
plt.xlabel('Arc length')
plt.ylabel('Velocity after b-pass')

plt.show()