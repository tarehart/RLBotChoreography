"""RLBotChoreography

Usage:
    ChoreographyHive [--num-bots=<num>] [--bot-folder=<folder>]
    ChoreographyHive (-h | --help)

Options:
    -h --help               Shows this help message.
    --num-bots=<num>        The number of bots to spawn [default: 10].
    --bot-folder=<folder>   Searches this folder for bot configs to use for names and appearances [default: .].
"""
import copy
import os
import sys
import time
from docopt import docopt
from importlib import reload
from queue import Queue 
from threading import Thread 

from rlbot.matchconfig.conversions import parse_match_config
from rlbot.parsing.agent_config_parser import load_bot_appearance
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs
from rlbot.parsing.rlbot_config_parser import create_bot_config_layout
from rlbot.setup_manager import SetupManager
from rlbot.utils.structures.start_match_structures import MAX_PLAYERS

import hivemind

################################################################

# TODO GUI
# Should allow you to choose choreography
# Maybe allow to specify bots?

################################################################

# VERSION 1

# Everything reloads.
# Allows for changing of the number of bots.

################################################################

def run_gui(queue):
    """
    Runs the simple gui.
    """
    import tkinter as tk

    def stop_hivemind():
        print("[RLBotChoreography]: Stopping Hivemind.")
        queue.put('STOP')

    root = tk.Tk()
    frame = tk.Frame(root)
    frame.pack()

    restart = tk.Button(frame, text="↻", command=stop_hivemind)
    restart.pack()

    root.mainloop()


def run_RLBotChoreography(queue):
    """
    If Hivemind breaks out of game_loop it is reloaded and recreated.
    """
    while True:
        arguments = docopt(__doc__) # Maybe use info from GUI instead?

        try:
            # TODO Somehow get to this information without creating an unnecessary object.
            # Consider a @staticmethod ?
            num_bots = hivemind.Hivemind(None).choreo.num_bots
            print('[RLBotChoreography]: Using the number of bots provided by the chosen choreography.')
        except AttributeError:
            num_bots = arguments['--num-bots']
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

        my_hivemind = hivemind.Hivemind(queue)
        my_hivemind.start()
        
        # Reloads hivemind for new changes to take place.
        reload(hivemind)


if __name__ == '__main__':

    # Runs GUI and Hivemind on two different threads.
    q = Queue()
    thread1 = Thread(target=run_RLBotChoreography, args=(q, ))
    thread1.start()
    thread2 = Thread(target=run_gui, args=(q, ))
    thread2.start()  
    q.join() 


################################################################

# VERSION 2

# Only the hivemind is reloaded. Match never restarts.

################################################################

# def run_gui(queue):
#     """
#     Runs the simple gui.
#     """
#     import tkinter as tk
#
#     def stop_hivemind():
#         print("[RLBotChoreography]: Stopping Hivemind.")
#         queue.put('STOP')
#
#     root = tk.Tk()
#     frame = tk.Frame(root)
#     frame.pack()
#
#     restart = tk.Button(frame, text="↻", command=stop_hivemind)
#     restart.pack()
#
#     root.mainloop()
#
#
# def run_hivemind(queue):
#     """
#     If Hivemind breaks out of game_loop it is reloaded and recreated.
#     """
#     while True:
#         my_hivemind = hivemind.Hivemind(queue)
#         my_hivemind.start()
#        
#         # Reloads hivemind for new changes to take place.
#         reload(hivemind)
#
#
# if __name__ == '__main__':
#     arguments = docopt(__doc__) # Maybe use info from GUI instead?
#
#     try:
#         # TODO Somehow get to this information without creating an unnecessary object.
#         # Consider a @staticmethod ?
#         num_bots = hivemind.Hivemind(None).choreo.num_bots
#         print('[RLBotChoreography]: Using the number of bots provided by the chosen choreography.')
#     except AttributeError:
#         num_bots = arguments['--num-bots']
#         print('[RLBotChoreography]: Using default or given number of bots.')
#     finally:
#         min_bots = min(int(num_bots), MAX_PLAYERS)
#
#     bot_directory = arguments['--bot-folder']
#     bundles = scan_directory_for_bot_configs(bot_directory)
#
#     # Set up RLBot.cfg
#     framework_config = create_bot_config_layout()
#     config_location = os.path.join(os.path.dirname(__file__), 'rlbot.cfg')
#     framework_config.parse_file(config_location, max_index=MAX_PLAYERS)
#     match_config = parse_match_config(framework_config, config_location, {}, {})
#
#     looks_configs = {idx: bundle.get_looks_config() for idx, bundle in enumerate(bundles)}
#     names = [bundle.name for bundle in bundles]
#
#     player_config = match_config.player_configs[0]
#     match_config.player_configs.clear()
#     for i in range(max(len(bundles), min_bots)):
#         copied = copy.copy(player_config)
#         if i < len(bundles):
#             copied.name = names[i]
#             # If you want to override bot appearances to get a certain visual effect, e.g. with
#             # specific boost colors, this is a good place to do it.
#             copied.loadout_config = load_bot_appearance(looks_configs[i], 0)
#         match_config.player_configs.append(copied)
#
#     manager = SetupManager()
#     manager.load_match_config(match_config, {})
#     manager.connect_to_game()
#     manager.start_match()
#
#     # Runs GUI and Hivemind on two different threads.
#     q = Queue()
#     thread1 = Thread(target=run_hivemind, args=(q, ))
#     thread1.start()
#     thread2 = Thread(target=run_gui, args=(q, ))
#     thread2.start()  
#     q.join() 