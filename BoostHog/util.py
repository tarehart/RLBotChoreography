import math

try:
    import numpy as np
except ImportError:
    try:
        from pip import main as pipmain
    except ImportError:
        from pip._internal import main as pipmain
        pipmain(['install', 'numpy'])
    try:
        import numpy as np
    except ImportError:
        raise ImportError("Failed to install numpy automatically, please install manually using: 'pip install numpy'")

from scipy.interpolate import interp1d


''' Utility functions '''
#Inspired by Marvin's bot Stick with modifications because I didn't understand what half of his stuff did :P

def a2(V):
    """Converts a Vector or normal list to a numpy array of size 2."""
    try:
        a = np.array([V[0], V[1]])
    except TypeError:
        a = np.array([V.x, V.y])
    return a


def a3(V):
    """Converts a Vector, rotator or normal list to a numpy array of size 3."""
    try:
        return np.array([V[0], V[1], V[2]])
    except TypeError:
        try:
            return np.array([V.x, V.y, V.z])
        except AttributeError:
            return np.array([V.Pitch, V.Yaw, V.Roll])


def a3l(L):
    """Converts List to numpy array."""
    return np.array([L[0], L[1], L[2]])


def a3r(R):
    """Converts Rotator to numpy array."""
    return np.array([R.pitch, R.yaw, R.roll])


def a3v(V):
    """Converts Vector3 to numpy array."""
    return np.array([V.x, V.y, V.z])

def dist2d(a, b=[0, 0]):
    """Distance/Magnitude in 2d."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def dist3d(a, b=[0, 0, 0]):
    """Distance/Magnitude in 3d."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def normalize(A):
    """Resizes the vector length to 1."""
    mag = np.linalg.norm(A)
    if mag == 0:
        mag = 1
    return A / mag


def turning_radius(speed):
    """Minimum turning radius given speed."""
    return -6.901E-11 * speed**4 + 2.1815E-07 * speed**3 - 5.4437E-06 * speed**2 + 0.12496671 * speed + 157


def turning_speed(radius):
    """Maximum speed given turning radius."""
    return 10.219 * radius - 1.75404E-2 * radius**2 + 1.49406E-5 * radius**3 - 4.486542E-9 * radius**4 - 1156.05


def get_steer(speed, desire_r):
    """aproximated steer for a desired curvature for given speed."""
    x = np.array([0, 500, 1000, 1500, 1750, 2300])
    y = np.array([0.0069, 0.00396, 0.00235, 0.001375, 0.0011, 0.00088])
    f = interp1d(x, y)
    
    max_curv    = f(speed)
    desire_curv = 1 / desire_r

    if max_curv >= desire_curv:
        return desire_curv / max_curv
    else:
        return 1.0


def radius_from_points(p0, p1, p2):
    """finds radius of circle defined by three points"""
    x0 = p0[0]
    y0 = p0[1]
    
    x1 = p1[0]
    y1 = p1[1]
    
    x2 = p2[0]
    y2 = p2[1]
    
    m0 = -(x1-x0)/(y1-y0)
    m1 = -(x2-x1)/(y2-y1)
    
    A = y2-y0 + m0*(x0+x1) - m1*(x1+x2)
    
    x = A / (2*(m0-m1))
    y = m0*(x-0.5*(x0+x1))+0.5*(y0+y1)
    
    r = math.sqrt((x-x0)**2+(y-y0)**2)
    
    return r


def orientMat(R):
    """converts from Euler angles to an orientation matrix."""
    pitch   = R[0]
    yaw     = R[1]
    roll    = R[2]

    CR = math.cos(roll)
    SR = math.sin(roll)
    CP = math.cos(pitch)
    SP = math.sin(pitch)
    CY = math.cos(yaw)
    SY = math.sin(yaw)

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
    """Transforms global/world into local coordinates."""
    return np.dot(A, V)


def world(V, A):
    """Transforms local into global/world coordinates."""
    return np.dot(V, A)

#https://en.wikipedia.org/wiki/B%C3%A9zier_curve
def bezier_quadratic(p0, p1, p2, t):
    """Returns a position on bezier curve defined by 3 points and t."""
    return p1 + (1-t)**2*(p0-p1) + t**2*(p2-p1)


def bezier_cubic(p0, p1, p2, p3, t):
    """Returns a position on bezier curve defined by 4 points and t."""
    return (1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t**2*p2 + t**3*p3
