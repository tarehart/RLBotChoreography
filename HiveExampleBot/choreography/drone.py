import numpy as np
from rlbot.agents.base_agent import SimpleControllerState


class Drone:
    def __init__(self, index: int, team: int):
        self.index: int = index
        self.team: int = team
        self.pos: np.ndarray = np.zeros(3)
        self.rot: np.ndarray = np.zeros(3)
        self.vel: np.ndarray = np.zeros(3)
        self.boost: float = 0.0
        self.orient_m: np.ndarray = np.identity(3)
        self.ctrl: SimpleControllerState = SimpleControllerState()
