'''Main bot file, just starts the hivemind helper process.'''

import os

from rlbot.agents.base_independent_agent import BaseIndependentAgent
from rlbot.botmanager.helper_process_request import HelperProcessRequest

class HiveBot(BaseIndependentAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)

    def get_helper_process_request(self) -> HelperProcessRequest:

        filepath = os.path.join(os.path.dirname(__file__), 'hivemind.py')
        # Differentiates between teams so each team has its own hivemind.
        key = 'Blue Hivemind' if self.team == 0 else 'Orange Hivemind'
        options = {}
        request = HelperProcessRequest(filepath, key, options=options)

        return request

    def run_independently(self, terminate_request_event):
        pass