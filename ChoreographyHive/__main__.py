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
import inspect
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

# TODO:
# - Remove docstring
# - Start GUI first
# - Choose module with choreography to import
# - Choose class within module
# - Allow to specify num-bots (Needs to somehow get the number from selected choreography)
# - Only start once selected

def setup_match():
    arguments = docopt(__doc__) # Maybe use info from GUI instead?

    try:
        num_bots = hivemind.Hivemind(None).choreo.get_num_bots() # FIXME
        print('[RLBotChoreography]: Using the number of bots provided by the chosen choreography.')
    except NotImplementedError:
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


def run_RLBotChoreography(queue):
    """
    If Hivemind breaks out of game_loop it is reloaded and recreated.
    """
    setup_match()

    while True:
        my_hivemind = hivemind.Hivemind(queue)
        my_hivemind.start()

        # Reloads hivemind for new changes to take place.
        reload(hivemind)
        
        # Checks what to do after hivemind died.
        command = queue.get()

        # HACK This might not be the most reliable way to do it. Any other ideas?
        if command == 'ALL':
            setup_match()


def run_gui(queue):
    """
    Runs the simple gui.
    """
    import tkinter as tk  

    def find_choreographies():
        """
        Finds all classes subclassing Choreography in the choreos directory.
        """
        # Importing the parent class.
        from choreography.choreography import Choreography
        import choreography.choreos

        choreographies = {}

        # HACK This seems non-standard, but it was the only thing that worked so far.
        for choreo in choreography.choreos.__all__:
            module = f'choreography.choreos.{choreo}'
            __import__(module, locals(), globals())

            # Finds the classes in the module.
            classes = inspect.getmembers(sys.modules[module], inspect.isclass)
            for name, obj in classes:
                # Checks whether the class subclasses Choreography.
                if issubclass(obj, Choreography):
                    # FIXME Watch out for name conflicts!
                    choreographies[name] = {'module': module, 'obj': obj}

        return choreographies

    def reload_hive():
        print("[RLBotChoreography]: Stopping Hivemind.")
        queue.put('STOP')
        # Reloading just the Hivemind.
        queue.put('HIVE')

    def reload_all():
        print("[RLBotChoreography]: Stopping Hivemind.")
        queue.put('STOP')
        print("[RLBotChoreography]: Reloading all.")
        queue.put('ALL')

    # TODO Make GUI look better.

    root = tk.Tk()
    frame = tk.Frame(root)
    frame.pack()

    # Hive reset button.
    button_reload_hive = tk.Button(frame, text="↻ Hivemind", command=reload_hive)
    button_reload_hive.pack()
        
    # All reset button.
    button_reload_all = tk.Button(frame, text="↻ All", command=reload_all)
    button_reload_all.pack()

    # Dropdown menu.
    menuvar = tk.StringVar(root)
    menuvar.set('LightfallChoreography') # set the default option
    choreographies = find_choreographies()
    dropMenu = tk.OptionMenu(frame, menuvar, *choreographies)
    dropMenu.pack()

    root.mainloop()


if __name__ == '__main__':

    # Runs GUI and Hivemind on two different threads.
    q = Queue()
    thread1 = Thread(target=run_gui, args=(q, ))
    thread1.start()  
    thread2 = Thread(target=run_RLBotChoreography, args=(q, ))
    #thread2.start()
    q.join()
