'''The Hivemind - Bot helper process.'''

import queue
import time

from rlbot.botmanager.agent_metadata import AgentMetadata
from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils import rate_limiter
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.structures.game_interface import GameInterface

import data
import brain
import actions
import numpy as np
from utils import a3l, world, local

class Hivemind(BotHelperProcess):

    def __init__(self, agent_metadata_queue, quit_event, options):
        super().__init__(agent_metadata_queue, quit_event, options)
        self.logger = get_logger('Hivemind')
        self.game_interface = GameInterface(self.logger)
        self.running_indices = set()

    def try_receive_agent_metadata(self):
        while True:  # will exit on queue.Empty
            try:
                single_agent_metadata: AgentMetadata = self.metadata_queue.get(timeout=0.1)
                self.running_indices.add(single_agent_metadata.index)
            except queue.Empty:
                return
            except Exception as ex:
                self.logger.error(ex)


    def start(self):
        """Runs once, sets up the hivemind and its agents."""
        # Prints stuff into the console.
        self.logger.info("Hivemind A C T I V A T E D")
        self.logger.info("Breaking the meta")
        self.logger.info("Welcoming r0bbi3")
        
        # Loads game interface.
        self.game_interface.load_interface()

        # Wait a moment for all agents to have a chance to start up and send metadata.
        time.sleep(1)
        self.try_receive_agent_metadata()
        
        # Runs the game loop where the hivemind will spend the rest of its time.
        self.game_loop()

            
    def game_loop(self):
        """The main game loop. This is where your hivemind code goes."""

        # Setting up rate limiter.
        rate_limit = rate_limiter.RateLimiter(120)

        # Setting up data.
        field_info = FieldInfoPacket()
        self.game_interface.update_field_info_packet(field_info)
        packet = GameTickPacket()
        self.game_interface.update_live_data_packet(packet)

        data.setup(self, packet, field_info, self.running_indices)

        self.ball.predict = BallPrediction()

        # MAIN LOOP:
        while True:
            # Updating the game packet from the game.
            self.game_interface.update_live_data_packet(packet)
    
            # Processing packet.
            data.process(self, packet)

            # Ball prediction.           
            self.game_interface.update_ball_prediction(self.ball.predict)

            # Rendering Ball prediction.
            locations = [step.physics.location for step in self.ball.predict.slices]
            self.game_interface.renderer.begin_rendering('ball prediction')
            self.game_interface.renderer.draw_polyline_3d(locations, self.game_interface.renderer.pink())
            self.game_interface.renderer.end_rendering()

            # Planning
            brain.plan(self)

            # For each drone under the hivemind's control, do something.
            for drone in self.drones:

                drone.ctrl = PlayerInput() # Basically the same as SimpleControllerState().
                '''
                {
                throttle:   float; /// -1 for full reverse, 1 for full forward
                steer:      float; /// -1 for full left, 1 for full right
                pitch:      float; /// -1 for nose down, 1 for nose up
                yaw:        float; /// -1 for full left, 1 for full right
                roll:       float; /// -1 for roll left, 1 for roll right
                jump:       bool;  /// true if you want to press the jump button
                boost:      bool;  /// true if you want to press the boost button
                handbrake:  bool;  /// true if you want to press the handbrake button
                use_item:   bool;  /// true if you want to use a rumble item
                }
                '''

                # Pizzatime is a debug mode. Don't ask me why I called it that. I must have been hungry or something.
                drone.pizzatime = True
                if drone.pizzatime:
                    # Turning in circles.
                    drone.ctrl.throttle = 1
                    drone.ctrl.steer = 1

                    # Rendering turn circles.
                    r = drone.turn_r
                    A = drone.orient_m

                    detail = 12
                    centre = world(A, drone.pos, a3l([0,r,0]))
                    points = np.zeros((detail,3))
                    theta  = np.linspace(0, 2*np.pi, detail)
                    points[:,0] += r*np.cos(theta)
                    points[:,1] += r*np.sin(theta)
                    points = np.dot(points, A)
                    points += centre

                    self.game_interface.renderer.begin_rendering("turn circles" + str(drone.index))
                    self.game_interface.renderer.draw_polyline_3d(points, self.game_interface.renderer.red())
                    self.game_interface.renderer.end_rendering()

                    # Test prints into console.
                    # print("drone index:", drone.index)
                    opp = self.opponents[0]
                    
                    # Testing reversibility of world and local functions
                    print(local(opp.orient_m, opp.pos, self.ball.pos))

                # Actual agent control.
                else:
                    drone.ctrl = actions.run(self, drone)
                        

                # Send the controls to the bots.
                self.game_interface.update_player_input(drone.ctrl, drone.index)

            # Rate limit sleep.
            rate_limit.acquire()