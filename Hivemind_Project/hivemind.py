'''Bot helper process.'''

from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.logging_utils import get_logger

import time
import queue
class Hivemind(BotHelperProcess):
    def __init__(self, agent_metadata_queue, quit_event, options):
        super().__init__(agent_metadata_queue, quit_event, options)
        self.logger = get_logger('Hivemind')
        self.game_interface = GameInterface(self.logger)

    def try_receive_agent_metadata(self):
        while not queue.Empty:
            single_agent_metadata: AgentMetadata = self.metadata_queue.get(timeout=0.1)
            self.running_indices.add(single_agent_metadata.index)
        return

    def start(self):
        self.logger.info("Hivemind A C T I V A T E D")

        self.game_interface.load_interface()

        # Wait a moment for all agents to have a chance to start up and send metadata
        time.sleep(1)
        self.try_receive_agent_metadata()
        self.game_loop()



    def game_loop(self):
        while not self.quit_event.is_set():
            self.logger.info("Welcoming r0bbi3")
            if self.communication.Empty:
                self.logger.info("Breaking the meta")
                self.communication.put({'target': [0,0,0]})