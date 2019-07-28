import numpy as np
from utils import a3l, cap

omega_max : float= 5.5
T_r : float = -36.07956616966136 # Torque coefficient for roll.
T_p : float = -12.14599781908070 # Torque coefficient for pitch.
T_y : float =   8.91962804287785 # Torque coefficient for yaw.
D_r : float =  -4.47166302201591 # Drag coefficient for roll.
D_p : float = -2.798194258050845 # Drag coefficient for pitch.
D_y : float = -1.886491900437232 # Drag coefficient for yaw.

class state:
    def __init__(self, omega = np.zeros(3), theta = np.identity(3)):
        self.omega = omega
        self.theta = theta

def aerial_control_predict(current : state, roll : float, pitch : float, yaw : float, dt : float):

    T = np.zeros((3, 3))
    T[0,0] = T_r
    T[1,1] = T_p
    T[2,2] = T_y

    D = np.zeros((3,3))
    D[0,0] = D_r
    D[1,1] = D_p * (1 - abs(pitch))
    D[2,2] = D_y * (1 - abs(yaw))

    # Compute the net torque on the car.
    tau = np.dot(D, np.dot(current.theta.T, current.omega))
    tau+= np.dot(T, a3l([roll, pitch, yaw]))
    tau = np.dot(T, tau)

    # Use the torque to get the update angular velocity.
    omega_next = current.theta + tau * dt

    # Prevent the angular velocity from exceeding a threshold.
    omega_next *= min(1.0, omega_max / np.linalg.norm(current.theta))

    # Compute the average angular velocity for this step
    omega_avg = 0.5 * (current.theta + omega_next)
    phi : float = np.linalg.norm(omega_avg) * dt

    omega_dt = np.array([
        [0.0, -omega_avg[2] * dt, omega_avg[1] * dt],
        [omega_avg[2] * dt, 0.0, -omega_avg[0] * dt],
        [-omega_avg[1] * dt, omega_avg[0] * dt, 0.0]
    ])

    R = np.identity(3)
    R += (np.sin(phi) / phi) * omega_dt
    R += (1.0 - np.cos(phi)) / (phi*phi) * np.dot(omega_dt, omega_dt)

    return state(omega_next, np.dot(R, current.theta))


def aerial_input_generate(omega_start : np.ndarray, omega_end : np.ndarray, theta_start : np.ndarray, dt : float):
    # Net torque in world coordinates.
    tau = (omega_end - omega_start) / dt

    # Ner torque in local coordinates.
    tau = np.dot(theta_start.T, tau)

    # Beggining-step angular velocity, in local coordinates.
    omega_local = np.dot(theta_start.T, omega_start)

    rhs = np.zeros(3)
    rhs[0] = tau[0] - D_r * omega_local[0]
    rhs[1] = tau[1] - D_p * omega_local[1]
    rhs[2] = tau[2] - D_y * omega_local[2]

    # User inputs: roll, pitch, yaw.
    u = np.zeros(3)
    u[0] = rhs[0] / T_r
    u[1] = rhs[1] / (T_p + np.sign(rhs[1]) * omega_local[1] * D_p) 
    u[2] = rhs[2] / (T_y - np.sign(rhs[2]) * omega_local[2] * D_y)

    # Ensure that values are between -1 and 1.
    u[0] = cap(u[0], -1, 1)
    u[1] = cap(u[1], -1, 1)
    u[2] = cap(u[2], -1, 1)

    return u


# TODO Make this work, and test it.
class AerialTurn_Control:
    def __init__(self, agent, orientation):
        self.agent = agent
        self.orientation = orientation

    def run(self):
        pass

    def render(self, s):
        s.renderer.begin_rendering('AieralTurn')
        s.renderer.draw_string_2d(10, 70, 1, 1, ('pitch: '+str(self.agent.ctrl.pitch)), s.renderer.white())
        s.renderer.draw_string_2d(10, 90, 1, 1, ('yaw: '+str(self.agent.ctrl.yaw)), s.renderer.white())
        s.renderer.draw_string_2d(10, 110, 1, 1, ('roll: '+str(self.agent.ctrl.roll)), s.renderer.white())
        s.renderer.end_rendering()