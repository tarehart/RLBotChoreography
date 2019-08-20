'''
Main bot file, just requests the hivemind helper process.
Your hivemind code goes in hivemind.py.
'''

import os

from rlbot.agents.base_independent_agent import BaseIndependentAgent
from rlbot.botmanager.helper_process_request import HelperProcessRequest

class HiveBot(BaseIndependentAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)

    def get_helper_process_request(self) -> HelperProcessRequest:
        """Requests a helper process"""

        # Filepath to the hivemind file. If you rename it, also rename it here.
        filepath = os.path.join(os.path.dirname(__file__), 'hivemind.py')

        # Differentiates between teams so each team has its own hivemind.
        # Make sure to make the keys something unique, otherwise other people's hiveminds could take over.
        key = 'Blue Example Hivemind' if self.team == 0 else 'Orange Example Hivemind'

        # Creates request for helper process.
        options = {}
        request = HelperProcessRequest(filepath, key, options=options)

        return request

    def run_independently(self, terminate_request_event):
        pass