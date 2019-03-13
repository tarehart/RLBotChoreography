"""Rocket League Functions"""

import numpy as np

def a3l(L):
    """converts list to numpy array"""
    return np.array([L[0], L[1], L[2]])

def a3r(R):
    """converts rotator to numpy array"""
    return np.array([R.pitch, R.yaw, R.roll])

def a3v(V):
    """converts vector3 to numpy array"""
    return np.array([V.x, V.y, V.z])