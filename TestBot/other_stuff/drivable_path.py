import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def bezier_cubic(p0, p1, p2, p3, n : int):
    """Returns a position on bezier curve defined by 4 points at t.

    Arguments:
        p0 {np.array} -- Coordinates of point 0.
        p1 {np.array} -- Coordinates of point 1.
        p2 {np.array} -- Coordinates of point 2.
        p3 {np.array} -- Coordinates of point 3.
        n {int} -- Number of points on the curve to generate.

    Returns:
        np.array -- Coordinates on the curve.
    """
    p0 = p0.reshape(p0.shape[0],1)
    p1 = p1.reshape(p1.shape[0],1)
    p2 = p2.reshape(p2.shape[0],1)
    p3 = p3.reshape(p3.shape[0],1)
    t = np.linspace(0.0, 1.0, n)
    path = (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3
    return path.T

'''
def OGH(p0, p1, v0, v1, t, t0=0, t1=1):
    """Optimized geometric Hermite curve."""
    p0 = p0.reshape(p0.shape[0],1)
    p1 = p1.reshape(p1.shape[0],1)
    v0 = v0.reshape(v0.shape[0],1)
    v1 = v1.reshape(v1.shape[0],1)

    s = (t-t0)/(t1-t0)
    a0 = (6*np.dot((p1-p0).T,v0)*np.dot(v1.T,v1) - 3*np.dot((p1-p0).T,v1)*np.dot(v0.T,v1)) / ((4*np.dot(v0.T,v0)*np.dot(v1.T,v1) - np.dot(v0.T,v1)*np.dot(v0.T,v1))*(t1-t0))
    a1 = (3*np.dot((p1-p0).T,v0)*np.dot(v0.T,v1) - 6*np.dot((p1-p0).T,v1)*np.dot(v0.T,v0)) / ((np.dot(v0.T,v1)*np.dot(v0.T,v1) - 4*np.dot(v0.T,v0)*np.dot(v1.T,v1))*(t1-t0))
    h0 = (2*s+1)*(s-1)*(s-1)
    h1 = (-2*s+3)*s*s
    h2 = (1-s)*(1-s)*s
    h3 = (s-1)*s*s

    plt.plot([p0[0],p1[0]], [p0[1],p1[1]], ':c')
    plt.plot([p0[0], (p0+v0)[0]], [p0[1], (p0+v0)[1]], '-g')
    plt.plot([p1[0], (p1+v1)[0]], [p1[1], (p1+v1)[1]], '-g')

    path = h0*p0 + h1*p1 + h2*v0*a0 + h3*v1*a1
    return path.T
'''

def get_path_length(path):
    a = path[:-1]
    b = path[1:]
    return np.sum(np.linalg.norm(b-a,axis=1))

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

# TODO Gradient constrain the velocities according to actual possible Rocket League accelerations
# https://samuelpmish.github.io/notes/RocketLeague/path_analysis/
# https://samuelpmish.github.io/notes/RocketLeague/ground_control/

n = 1000
t = np.linspace(0, 1, n)


# OGH
'''
p0 = np.array([0,0,0])
p1 = np.array([1000,0,0])
v0 = np.array([100,400,0])
v1 = np.array([400,-100,0])

path0 = OGH(p0, p1, v0, v1, t)
print('path0:',get_path_length(path0))
path0_k = get_curvature(path0)
path0_v = max_speed_from_curve(path0_k)
'''

# Bezier
p0 = np.array([0,0,0])
p1 = np.array([100,-500,0])
p2 = np.array([400,-500,0])
p3 = np.array([1000,0,0])

path1 = bezier_cubic(p0, p1, p2, p3, n)
print('path1:',get_path_length(path1))
path1_k = get_curvature(path1)
path1_v = max_speed_from_curve(path1_k)


# Plotting
plt.subplot(3,1,1)
plt.ylabel('Path')
#plt.plot(path0[:,0],path0[:,1])
plt.plot(path1[:,0],path1[:,1])

plt.subplot(3,1,2)
plt.ylabel('Curvature')
#plt.plot(t,path0_k)
plt.plot(t,path1_k)

plt.subplot(3,1,3)
plt.ylabel('Curvature-based velocity')
#plt.plot(t,path0_v)
plt.plot(t,path1_v)
plt.show()