'''The Hivemind - Bot helper process.'''

'''Hey TGD, this is just the shell to make the thing run; the bots do nothing. - Will'''

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

from utils import a3v
import data
import brain

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
        self.logger.info("Welcoming @r0bbi3#0269")
        
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

            brain.think(self)

            for drone in self.drones:
                drone.ctrl = PlayerInput()
                if drone.role is not None:
                    drone.role.execute(self, drone)
                self.game_interface.update_player_input(drone.ctrl, drone.index)

            self.draw_debug()

            # Rate limit sleep.
            rate_limit.acquire()


    def draw_debug(self):
        self.game_interface.renderer.begin_rendering()
        path = [a3v(step.physics.location) for step in self.ball.predict.slices]
        self.game_interface.renderer.draw_polyline_3d(path, self.game_interface.renderer.pink())

        for drone in self.drones:
            if drone.role is not None:
                self.game_interface.renderer.draw_string_3d(drone.pos, 1, 1, drone.role.name, self.game_interface.renderer.white())
        self.game_interface.renderer.end_rendering()

"""
ball_prediction_struct = {
    'slices': {
        'physics': {
            'location': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0},
            'velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'angular_velocity': {'x': 0.0, 'y': 0.0, 'z': 0.0}
        },
        'game_seconds': 0.0,
    },
    { ... }
    'num_slices': 360,
}
"""
