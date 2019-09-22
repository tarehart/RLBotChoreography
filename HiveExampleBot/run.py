import copy
import os

from rlbot.matchconfig.conversions import parse_match_config
from rlbot.parsing.agent_config_parser import load_bot_appearance
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs
from rlbot.parsing.rlbot_config_parser import create_bot_config_layout
from rlbot.setup_manager import SetupManager

if __name__ == '__main__':

    # Set up RLBot.cfg
    framework_config = create_bot_config_layout()
    config_location = os.path.realpath('rlbot.cfg')
    framework_config.parse_file(config_location, max_index=64)
    match_config = parse_match_config(framework_config, config_location, {}, {})

    bundles = scan_directory_for_bot_configs("C:/Users/tareh/code/LeaguePlay/bots")
    looks_configs = {idx: bundle.get_looks_config() for idx, bundle in enumerate(bundles)}
    names = [bundle.name for bundle in bundles]

    player_config = match_config.player_configs[0]
    match_config.player_configs.clear()
    for i in range(len(bundles)):
        copied = copy.copy(player_config)
        copied.name = names[i]
        copied.loadout_config = load_bot_appearance(looks_configs[i], 0)
        match_config.player_configs.append(copied)

    manager = SetupManager()
    manager.load_match_config(match_config, {})
    manager.connect_to_game()
    manager.start_match()
    manager.launch_bot_processes()
    manager.infinite_loop()  # Runs forever until interrupted
