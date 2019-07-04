'''Bot helper process.'''

from rlbot.botmanager.bot_helper_process import BotHelperProcess
from rlbot.utils.structures.game_interface import GameInterface
from rlbot.utils.logging_utils import get_logger

import asyncio
import time
import queue
import websockets

class Hivemind(BotHelperProcess):
    def __init__(self, agent_metadata_queue, quit_event, options):
        super().__init__(agent_metadata_queue, quit_event, options)
        self.logger = get_logger('hivemind') #This was originally 'scratch_mgr'. Not sure what it does.
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
        self.logger.info("Awaking Hivemind")

        self.game_interface.load_interface()

        # Wait a moment for all agents to have a chance to start up and send metadata
        time.sleep(1)
        self.try_receive_agent_metadata()

        self.logger.info(self.running_indices)

        asyncio.get_event_loop().run_until_complete(self.game_loop())

    async def game_loop(self):
        while not self.quit_event.is_set():
            print("Game loop function running!")