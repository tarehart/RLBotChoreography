import numpy as np

from rlbot.agents.base_agent import SimpleControllerState
from rlbot.utils.game_state_util import GameState, CarState, Physics, Vector3, Rotator, BallState
from rlbot.utils.structures.game_interface import GameInterface

from choreography.choreography import Choreography
from choreography.drone import seek_pos, normalise
from choreography.group_step import BlindBehaviorStep, DroneListStep, StepResult, PerDroneStep


class Boids(Choreography):
    """
    Boids in RLBot!
    Clip: https://gfycat.com/disguisedincompatiblefeline-rocketleague
    Based on: https://www.red3d.com/cwr/boids/
    """

    def __init__(self, game_interface: GameInterface):
        super().__init__()
        self.game_interface = game_interface

    def generate_sequence(self):
        self.sequence.clear()

        self.sequence.append(DroneListStep(self.hide_ball))
        # self.sequence.append(DroneListStep(self.scatter))
        self.sequence.append(DroneListStep(self.drones_are_boids))

        
    def hide_ball(self, packet, drones, start_time) -> StepResult:
        """
        Places the ball above the roof of the arena to keep it out of the way.
        """
        self.game_interface.set_game_state(GameState(ball=BallState(physics=Physics(
            location=Vector3(0, 0, 3000),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)))))
        return StepResult(finished=True)

    
    def scatter(self, packet, drones, start_time) -> StepResult:
        """
        Scatters the bots around the field randomly.
        """
        car_states = {}
        for drone in drones:
            x = np.random.uniform(-4000, 4000)
            y = np.random.uniform(-5000, 5000)
            rot = np.random.uniform(-np.pi, np.pi)

            car_states[drone.index] = CarState(
                Physics(location=Vector3(x, y, 20),
                        velocity=Vector3(0, 0, 0),
                        rotation=Rotator(0, rot, 0)))
        self.game_interface.set_game_state(GameState(cars=car_states))

        return StepResult(finished=True)


    def drones_are_boids(self, packet, drones, start_time) -> StepResult:
        """
        Controls the drones to act like boids.
        """
        # Parameters:
        PERCEPTION_DIS = 1000
        ALIGNMENT_MUL = 300
        COHESION_MUL = 200
        SEPARATION_MUL = 350
        AVOID_WALL_MUL = 1000

        for drone in drones:
            # Resetting drone controller.
            drone.ctrl = SimpleControllerState()
            
            # Creating "forces"
            alignment_vec = np.zeros(3)
            cohesion_vec = np.zeros(3)
            separation_vec = np.zeros(3)
            avoid_walls_vec = np.zeros(3)

            others = 0 # The amount of drones in perception dist.
            for other in drones:
                # Skip if the other is also the drone.
                if other is drone: continue
                
                other_to_drone = drone.pos - other.pos
                distance = np.linalg.norm(other_to_drone)

                # Skip if other is too far.
                if distance > PERCEPTION_DIS: continue

                # Increment others.
                others += 1

                # Alignment
                alignment_vec += other.vel
                # Cohesion
                cohesion_vec += other.pos
                # Separation
                separation_vec += other_to_drone / distance**2
            
            # Avoid Walls.
            if drone.pos[0] < -2800:
                avoid_walls_vec += np.array([1,0,0])
            elif drone.pos[0] > 2800:
                avoid_walls_vec += np.array([-1,0,0])

            if drone.pos[1] < -3800:
                avoid_walls_vec += np.array([0,1,0])
            elif drone.pos[1] > 3800:
                avoid_walls_vec += np.array([0,-1,0])
                
            # Averaging out cohesion_vec 
            # and making it relative to drone.
            if others > 0: cohesion_vec / others
            cohesion_vec -= drone.pos

            # Create seek target.
            target = np.zeros(3)
            target += ALIGNMENT_MUL * normalise(alignment_vec)
            target += COHESION_MUL * normalise(cohesion_vec)
            target += SEPARATION_MUL * normalise(separation_vec)
            target += AVOID_WALL_MUL * normalise(avoid_walls_vec)

            target += drone.pos

            # Follow target.
            seek_pos(drone, target, max_speed=1000)

        # Never finishes.
        return StepResult(finished=False)

