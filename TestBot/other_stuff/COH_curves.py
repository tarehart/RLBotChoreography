'''Composite Optimised Geometric Hermite Curves'''
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.104.1622&rep=rep1&type=pdf

import numpy as np
import matplotlib.pyplot as plt

def counterclockwise_angle(v):
    """Returns the counterclockwise angle of a vector measured from the positive x-axis."""
    angle = np.arctan2(v[1],v[0])
    return angle[0] if angle >= 0 else 2*np.pi + angle[0]

# TODO Make sure this is correct because it might not be.
def angle_between_vectors(a, b):
    """Returns the counterclockwise angle in radians between vectors a and b, measured from a to b."""
    angle_a = counterclockwise_angle(a)
    angle_b = counterclockwise_angle(b)
    angle = angle_b - angle_a
    return angle if angle >= 0 else 2*np.pi + angle

def vector_from_angle(angle : float, magnitude : float = 1):
    """Returns a vector with a given angle and length"""
    return magnitude * np.array([[np.cos(angle)],[np.sin(angle)]])

def Q(p0, p1, v0, v1, t0, t1, t):
    """Basic Hermite curve."""
    s = (t-t0)/(t1-t0)
    h0 = (2*s+1)*(s-1)*(s-1)
    h1 = (-2*s+3)*s*s
    h2 = (1-s)*(1-s)*s*(t1-t0)
    h3 = (s-1)*s*s*(t1-t0)
    return h0*p0 + h1*p1 + h2*v0 + h3*v1

def OGH(p0, p1, v0, v1, t0, t1, t):
    """Optimized geometric Hermite curve."""
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

    return h0*p0 + h1*p1 + h2*v0*a0 + h3*v1*a1

def COH(p0, p1, v0, v1, t0, t1, t):
    """Composite optimized geometric Hermite curve."""
    # theta is the counterclockwise angle from the vector p0p1 to v0.
    # phi is the counterclockwise angle from the vector p0p1 to v1.
    theta : float = angle_between_vectors(p1-p0, v0)
    phi : float = angle_between_vectors(p1-p0, v1)

    print("theta: {}pi".format(theta))
    print("phi  : {}pi".format(phi))

    # alpha is the counterclockwise angle of the vector p0p1 from the x-axis.
    alpha : float = counterclockwise_angle(p1-p0)

    # M0: simple OGH curve.
    if 3*np.cos(theta) > np.cos(theta - 2*phi) and 3*np.cos(phi) > np.cos(phi - 2*theta):
        print("M0")
        plt.title("M0")
        return OGH(p0, p1, v0, v1, t0, t1, t)

    # M1: two-segment COH curve.
    elif (0 <= theta <= np.pi/6) and (np.pi/3 <= phi <= 2*np.pi/3):
        print("M1")
        plt.title("M1")

        pT = p1 - vector_from_angle(phi/2 + alpha, np.linalg.norm(p1-p0)/3)
        beta : float = angle_between_vectors(pT-p0,p1-pT)
        gamma : float = counterclockwise_angle(pT-p0)
        vT = vector_from_angle(beta/2 + gamma)

        return np.concatenate([OGH(p0,pT,v0,vT,t0,t1,t),OGH(pT,p1,vT,v1,t0,t1,t)],axis=1)

    # M2: two-segment COH curve.
    elif ((0 <= theta <= np.pi/3) and (np.pi <= phi <= 5*np.pi/3)) or ((np.pi/3 <= theta <= 2*np.pi/3) and (4*np.pi/3 <= phi <= 5*np.pi/3)):
        print("M2")
        plt.title("M2")

        A : float = np.pi/18 if theta < np.pi/9 else theta/2
        B : float = 2*np.pi - phi - (2*np.pi-phi+theta-A)/3
        C : float = np.pi - A - B

        c : float = np.linalg.norm(p1-p0)
        b : float = c * np.sin(B) / np.sin(C)

        pT = p0 + vector_from_angle(A + alpha, b)
        vT = vector_from_angle(A - (2*np.pi-phi+theta-A)/3)
        
        return np.concatenate([OGH(p0,pT,v0,vT,t0,t1,t),OGH(pT,p1,vT,v1,t0,t1,t)],axis=1)
    
    # M3: three-segment COH curve.
    elif (0 <= theta <= np.pi/3) and (np.pi/3 <= phi <= np.pi):
        print("M3")
        plt.title("M3")

        beta : float = phi/3
        a1 : float = (theta-beta)/2 - np.pi/18 if (theta-beta)/2 - np.pi >= 0 else (theta-beta)/2 + 35*np.pi/18
        a3 : float = 17*np.pi/9
        a5 : float = phi - beta
        a4 : float = (a3 + a5)/2 - np.pi

        if np.pi/18 < abs(a3 - a1) < np.pi:
            A : float = abs(a3 - a1)
        elif np.pi < abs(a3 - a1) < 35*np.pi/18:
            A : float = 2*np.pi - abs(a3 - a1)
        else:
            A : float = np.pi/18

        a2 : float = a1 - 2*A

        pT0 = p0 + vector_from_angle(alpha + a1, np.linalg.norm(p1-p0)/(2*np.cos(a1)))
        vT0 = vector_from_angle(alpha + a2)

        L : float = a3 - a5 - np.pi
        l : float = np.linalg.norm(p1-pT0)
        K : float = angle_between_vectors(p0-p1,pT0-p1)
        k : float = l*np.sin(2*np.pi-a3+K) / np.sin(L)

        pT1 = p1 - vector_from_angle(alpha + a5, k)
        vT1 = vector_from_angle(alpha + a4)

        return np.concatenate([OGH(p0,pT0,v0,vT0,t0,t1,t),OGH(pT0,pT1,vT0,vT1,t0,t1,t),OGH(pT1,p1,vT1,v1,t0,t1,t)],axis=1)

    elif (np.pi/3 <= theta <= 2*np.pi/3) and (0 <= phi <= 2*np.pi/3):
        print("M4")
        plt.title("M4")

        l : float = np.linalg.norm(p1-p0)

        pT0 = p0 + vector_from_angle(alpha + theta/2, l/3)
        pT1 = p1 - vector_from_angle(alpha + phi/2, l/6)

        vT0 = vector_from_angle(alpha + theta/2 - angle_between_vectors(pT1-pT0, pT0-p0)/2)
        vT1 = vector_from_angle(alpha + phi/2 - angle_between_vectors(pT1-pT0, p1-pT1)/2)

        return np.concatenate([OGH(p0,pT0,v0,vT0,t0,t1,t),OGH(pT0,pT1,vT0,vT1,t0,t1,t),OGH(pT1,p1,vT1,v1,t0,t1,t)],axis=1)

    elif ((np.pi/3 <= theta <= 2*np.pi/3) and (np.pi <= phi <= 4*np.pi/3)) or ((2*np.pi/3 <= theta <= np.pi) and (np.pi <= phi <= 5*np.pi/3)):
        print("M5")
        plt.title("M5")

        r = np.linalg.norm(p1-p0)/2
        beta : float = (theta - phi + 2*np.pi)/6

        A = 3*beta - theta + np.pi/2
        A_prime = (np.pi - A) / 2
        A_side = np.sqrt(2*r*r - r*r*np.cos(A))
        k = A_side*np.sin(np.pi/2-A_prime) / np.sin(np.pi-2*beta)

        pT0 = p0 + vector_from_angle(alpha + theta - beta, k)
        vT0 = vector_from_angle(alpha + theta - 2*beta)        

        B = 3*beta + phi - 3*np.pi/2
        B_prime = (np.pi - B) / 2
        B_side = np.sqrt(2*r*r - r*r*np.cos(B))
        l = B_side*np.sin(np.pi/2-B_prime) / np.sin(np.pi-2*beta)
        
        pT1 = p1 - vector_from_angle(alpha + phi + beta, l)
        vT1 = vector_from_angle(alpha + theta - 4*beta)

        return np.concatenate([OGH(p0,pT0,v0,vT0,t0,t1,t),OGH(pT0,pT1,vT0,vT1,t0,t1,t),OGH(pT1,p1,vT1,v1,t0,t1,t)],axis=1)
    
    elif (2*np.pi/3 <= theta <= np.pi) and (np.pi/6 <= phi <= 2*np.pi/3):
        print("M6")
        plt.title("M6")

        #TODO Still sometimes breaks.
        
        a5 = phi/2
        beta = (2*np.pi + a5 - theta)/5
        l = np.linalg.norm(p1-p0)

        print("a5",a5)
        print("beta",beta)
        print("l",l)

        pT0 = p0 + vector_from_angle(alpha + theta + beta, l/2)
        vT0 = vector_from_angle(alpha + theta + 2*beta)

        a = np.sqrt(l*l*(5/4 - np.cos(theta - beta)))
        A = np.pi - 2*beta + np.arccos((a*a - 3*l*l/4) / (a*l))
        x = a * np.sin(A) / np.sin(np.pi - 2*beta)

        pT1 = p1 - vector_from_angle(alpha + a5, x)
        vT1 = vector_from_angle(alpha + theta + 4*beta)

        return np.concatenate([OGH(p0,pT0,v0,vT0,t0,t1,t),OGH(pT0,pT1,vT0,vT1,t0,t1,t),OGH(pT1,p1,vT1,v1,t0,t1,t)],axis=1)

    else:
        print("WIP")
        # TODO Do the other methods.
        # TODO figure out the reflecion stuff and other transformations.


def test(theta_min, theta_max, phi_min, phi_max):
    theta = np.random.uniform(theta_min, theta_max)
    phi = np.random.uniform(phi_min, phi_max)

    p0 = np.array([[-10], [0]])     #np.random.uniform(-10,10,size=(2,1))
    p1 = np.array([[10], [0]])      #np.random.uniform(-10,10,size=(2,1))

    alpha = counterclockwise_angle(p1-p0)

    v0 = vector_from_angle(alpha + theta)
    v1 = vector_from_angle(alpha + phi)

    t0 = 0
    t1 = 1

    n : int = 1000
    a = np.linspace(t0, t1, n)
    b = COH(p0, p1, v0, v1, t0, t1, a)

    plt.plot(b[0], b[1], '-b')
    plt.show()

def test_all():
    test(-1,1,-1,1)                             # M0
    test(0,np.pi/6,np.pi/3,2*np.pi/3)           # M1
    test(0,np.pi/3,np.pi,5*np.pi/3)             # M2 part 1
    test(np.pi/3,2*np.pi/3,4*np.pi/3,5*np.pi/3) # M2 part 2
    test(0,np.pi/3,np.pi/3,np.pi)               # M3
    test(np.pi/3,2*np.pi/3,0,2*np.pi/3)         # M4
    test(np.pi/3,2*np.pi/3,np.pi,4*np.pi/3)     # M5 part 1
    test(2*np.pi/3,np.pi,np.pi,5*np.pi/3)       # M5 part 2
    test(2*np.pi/3,np.pi,np.pi/6,2*np.pi/3)     # M6


test_all()