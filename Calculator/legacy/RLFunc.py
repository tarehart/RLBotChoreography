"""Rocket League Functions"""

import numpy as np
from math               import sin, cos
from scipy.interpolate  import interp1d

def a3l(L):
    """converts list to numpy array"""
    return np.array([L[0], L[1], L[2]])

def a3r(R):
    """converts rotator to numpy array"""
    return np.array([R.pitch, R.yaw, R.roll])

def a3v(V):
    """converts vector3 to numpy array"""
    return np.array([V.x, V.y, V.z])

def orient_matrix(R):
    """converts from Euler angles to an orientation matrix"""
    pitch   = R[0]
    yaw     = R[1]
    roll    = R[2]

    CR = cos(roll)
    SR = sin(roll)
    CP = cos(pitch)
    SP = sin(pitch)
    CY = cos(yaw)
    SY = sin(yaw)

    A = np.zeros((3,3))

    #front direction
    A[0][0] = CP * CY
    A[0][1] = CP * SY
    A[0][2] = SP 

    #right direction
    A[1][0] = CY * SP * SR - CR * SY
    A[1][1] = SY * SP * SR + CR * CY
    A[1][2] = -CP * SR

    #up direction
    A[2][0] = -CR * CY * SP - SR * SY
    A[2][1] = -CR * SY * SP + SR * CY
    A[2][2] = CP * CR

    return A

def local(V, A):
    """transforms global/world into local coordinates"""
    return np.dot(A, V)


def world(V, A):
    """transforms local into global/world coordinates"""
    return np.dot(V, A)


def get_steer(v, r):
    """aproximated steer for a desired curvature and velocity."""
    #interpolation of graph for max curvature given speed
    s = np.array([0, 500, 1000, 1500, 1750, 2300])
    k = np.array([0.0069, 0.00396, 0.00235, 0.001375, 0.0011, 0.00088])
    f = interp1d(s, k)

    max_k   = f(np.linalg.norm(v))
    want_k  = 1 / r

    if max_k >= want_k:
        #curvature is roughly proportional to steer
        return want_k / max_k
    else:
        return 1.0

def turn_r(v):
    """minimum turning radius for given velocity"""
    s = np.linalg.norm(v)
    return -6.901E-11 * s**4 + 2.1815E-07 * s**3 - 5.4437E-06 * s**2 + 0.12496671 * s + 157

def radius_from_points(A,B,C):
    """finds the radius of a circle defined by three points"""
    #the centre of the circle is the intersection of the perpendicular bisectors to AB and BC
    
    midAB = 0.5*(A+B)
    midBC = 0.5*(B+C)
    
    slopeAB = (B[1]-A[1])/(B[0]-A[0])
    slopeBC = (C[1]-B[1])/(C[0]-B[0])
    
    slopeABperp = -1 / slopeAB
    slopeBCperp = -1 / slopeBC
    
        #y - y1 = m(x - x1)
    #y - midAB[1] = slopeABperp*(x - midAB[0])
    #y - midBC[1] = slopeBCperp*(x - midBC[0])
    
        #solve for x
    #slopeABperp*(x - midAB[0]) + midAB[1] = slopeBCperp*(x - midBC[0]) + midBC[1]
    #slopeABperp*(x - midAB[0]) - slopeBCperp*(x - midBC[0]) = midBC[1] - midAB[1]
    #slopeABperp*x - slopeBCperp*x = midBC[1] - midAB[1] + slopeABperp*midAB[0] - slopeBCperp*midBC[0]
    #x*(slopeABperp - slopeBCperp) = slopeABperp*midAB[0] - midAB[1] - slopeBCperp*midBC[0] + midBC[1]
    
    x = (slopeABperp*midAB[0] - midAB[1] - slopeBCperp*midBC[0] + midBC[1])/(slopeABperp - slopeBCperp)
    y = slopeABperp*(x - midAB[0]) + midAB[1]
    O = np.array([x,y])
    r = np.linalg.norm(O-A)
    
    return r

def gen_circle_points(r,centre,A,n):
    """generates n evenly spaced points on the circle in 3D"""
    points = np.zeros((n+1,3))
    theta  = np.linspace(0,2*np.pi,n+1)
    points[:,0] += r*np.cos(theta)
    points[:,1] += r*np.sin(theta)
    points = np.dot(points,A)
    points += centre
    return points

def bezier_quadratic(p0, p1, p2, t):
    """returns a position on bezier curve defined by 3 points at t"""
    return p1 + (1-t)**2*(p0-p1) + t**2*(p2-p1)

def bezier_cubic(p0, p1, p2, p3, t):
    """returns a position on bezier curve defined by 4 points at t"""
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3
