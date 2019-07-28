'''The Hivemind - Bot helper process.'''

# Importing RLBot stuff.
from rlbot.botmanager.agent_metadata import AgentMetadata
from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils import rate_limiter
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from rlbot.utils.structures.game_interface import GameInterface

# Importing internal hivemind files.
import data
import brain

# Importing utility functions.
import numpy as np
from utils import a3l, world, local

# Other imports.
import queue
import time
import random


class Hivemind(BotHelperProcess):
    # TODO Maybe use __slots__ for better performance?

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
        message = random.choice([
            "Breaking the meta",
            "Welcoming r0bbi3",
            "Annoying chip by reinventing the wheel",
            "Actually texting her",
            "Banning anime",
            "Killing that guy",
            "Trying to pronounce jeroen",
            "Getting banned by Redox",
            "Becomind a mod",
        ])
        self.logger.info(message)
        
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
        # https://github.com/RLBot/RLBotPythonExample/wiki/Ball-Path-Prediction


        # MAIN LOOP:
        while True:
            # Updating the game packet from the game.
            self.game_interface.update_live_data_packet(packet)
    
            # Processing packet.
            data.process(self, packet)

            # Ball prediction.           
            self.game_interface.update_ball_prediction(self.ball.predict)

            # Planning.
            brain.plan(self)

            # Rendering.
            self.render_debug(self.game_interface.renderer)

            # For each drone under the hivemind's control, do something.
            for drone in self.drones:

                # The controls are reset each frame.
                drone.ctrl = PlayerInput() # Basically the same as SimpleControllerState().

                # Role execution.
                if drone.role is not None:
                    drone.role.execute(self, drone)
                    
                    self.render_role(self.game_interface.renderer, drone)
                    
                        

                # Send the controls to the bots.
                self.game_interface.update_player_input(drone.ctrl, drone.index)

            # Rate limit sleep.
            rate_limit.acquire()


    def render_debug(hive, rndr):
        """Debug rendering for all manner of things.
        
        Arguments:
            hive {Hivemind} -- The hivemind.
            rndr {?} -- The renderer.
        """
        # Rendering Ball prediction.
        locations = [step.physics.location for step in hive.ball.predict.slices]
        rndr.begin_rendering('ball prediction')
        rndr.draw_polyline_3d(locations, rndr.pink())
        rndr.end_rendering()


    def render_role(hive, rndr, drone):
        """Renders roles above the drones.
        
        Arguments:
            hive {Hivemind} -- The hivemind.
            rndr {?} -- The renderer.
            drone {Drone} -- The drone who's role is being rendered.
        """
        # Rendering role names above drones.
        above = drone.pos + a3l([0,0,100])
        rndr.begin_rendering(f'role_{hive.team}_{drone.index}')
        rndr.draw_string_3d(above, 1, 1, drone.role.name, rndr.cyan())
        rndr.end_rendering()

