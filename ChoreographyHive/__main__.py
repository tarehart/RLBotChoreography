"""RLBotChoreography

Usage:
    ChoreographyHive [--min-bots=<min>] [--bot-folder=<folder>]
    ChoreographyHive (-h | --help)

Options:
    -h --help               Shows this help message.
    --min-bots=<min>        The minimum number of bots to spawn [default: 10].
    --bot-folder=<folder>   Searches this folder for bot configs to use for names and appearances [default: .].
"""
import copy
import os
import sys
from docopt import docopt

from rlbot.matchconfig.conversions import parse_match_config
from rlbot.parsing.agent_config_parser import load_bot_appearance
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs
from rlbot.parsing.rlbot_config_parser import create_bot_config_layout
from rlbot.setup_manager import SetupManager
from rlbot.utils.structures.start_match_structures import MAX_PLAYERS

from hivemind import Hivemind

if __name__ == '__main__':

    arguments = docopt(__doc__)

    try:
        # TODO Somehow get to this information without creating an unnecessary object.
        num_bots = Hivemind().choreo.num_bots
        print('[RLBotChoreography]: Using the number of bots provided by the chosen choreography.')
    except AttributeError:
        num_bots = arguments['--min-bots']
        print('[RLBotChoreography]: Using default or given number of bots.')
    finally:
        min_bots = min(int(num_bots), MAX_PLAYERS)

    bot_directory = arguments['--bot-folder']
    bundles = scan_directory_for_bot_configs(bot_directory)

    # Set up RLBot.cfg
    framework_config = create_bot_config_layout()
    config_location = os.path.join(os.path.dirname(__file__), 'rlbot.cfg')
    framework_config.parse_file(config_location, max_index=MAX_PLAYERS)
    match_config = parse_match_config(framework_config, config_location, {}, {})

    looks_configs = {idx: bundle.get_looks_config() for idx, bundle in enumerate(bundles)}
    names = [bundle.name for bundle in bundles]

    player_config = match_config.player_configs[0]
    match_config.player_configs.clear()
    for i in range(max(len(bundles), min_bots)):
        copied = copy.copy(player_config)
        if i < len(bundles):
            copied.name = names[i]
            # If you want to override bot appearances to get a certain visual effect, e.g. with
            # specific boost colors, this is a good place to do it.
            copied.loadout_config = load_bot_appearance(looks_configs[i], 0)
        match_config.player_configs.append(copied)

    manager = SetupManager()
    manager.load_match_config(match_config, {})
    manager.connect_to_game()
    manager.start_match()

    hivemind = Hivemind()
    hivemind.start()
