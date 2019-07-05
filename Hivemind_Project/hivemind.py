'''Bot helper process.'''

import queue
import time

from rlbot.botmanager.agent_metadata import AgentMetadata
from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils import rate_limiter
from rlbot.utils.logging_utils import get_logger
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.game_interface import GameInterface

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
        self.logger.info("Hivemind A C T I V A T E D")
        self.logger.info("Breaking the meta")
        self.logger.info("Welcoming r0bbi3")
        
        self.game_interface.load_interface()

        # Wait a moment for all agents to have a chance to start up and send metadata
        time.sleep(1)
        self.try_receive_agent_metadata()

        self.game_loop()

            
    def game_loop(self):
        rate_limit = rate_limiter.RateLimiter(120)
        while True:
            packet = GameTickPacket()
            self.game_interface.update_live_data_packet(packet)

            for index in self.running_indices:

                player_input = PlayerInput()
                player_input.throttle = 1.0

                if index == 0:
                    player_input.steer = 1.0
                elif index == 1:
                    player_input.steer = -1.0
                else:
                    player_input.steer = 0.0
                    
                self.game_interface.update_player_input(player_input, index)

            rate_limit.acquire()