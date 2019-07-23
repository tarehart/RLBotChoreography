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
            render_debug(self.game_interface.renderer, self, drone)

            # For each drone under the hivemind's control, do something.
            for drone in self.drones:

                # The controls are reset each frame.
                drone.ctrl = PlayerInput() # Basically the same as SimpleControllerState().

                # Role execution.
                if drone.role is not None:
                    drone.role.execute(self, drone)
                    
                    render_role(self.game_interface.renderer, self, drone)
                    
                        

                # Send the controls to the bots.
                self.game_interface.update_player_input(drone.ctrl, drone.index)

            # Rate limit sleep.
            rate_limit.acquire()

def render_debug(renderer, hive, drone):
    # TODO Add Docstring
    # Rendering Ball prediction.
    locations = [step.physics.location for step in hive.ball.predict.slices]
    renderer.begin_rendering('ball prediction')
    renderer.draw_polyline_3d(locations, renderer.pink())
    renderer.end_rendering()

    # Rendering naive prediction
    # FIXME Once naive prediction is correctly implemented.
    '''
    self.game_interface.renderer.begin_rendering('opponent prediction')
    for opponent in hive.opponents:
        renderer.draw_polyline_3d(opponent.predict, renderer.blue())
    renderer.end_rendering()
    '''

def render_role(renderer, hive, drone):
    # TODO Add Docstring
    # Rendering role names above drones.
    above = drone.pos + a3l([0,0,100])
    renderer.begin_rendering("role" + str(hive.team) + str(drone.index))
    renderer.draw_string_3d(above, 1, 1, drone.role.name, renderer.cyan())
    renderer.end_rendering()

