"""RLBotChoreography

Usage:
    ChoreographyHive [--bot-folder=<folder>]
    ChoreographyHive (-h | --help)

Options:
    -h --help               Shows this help message.
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
# - Get info from GUI thread to RLBotChoreo thread
# - Import correct module in hivemind and use right choreography obj
# - Prettify GUI

def setup_match():
    arguments = docopt(__doc__) # Maybe use info from GUI instead?

    # try:
    #     num_bots = hivemind.Hivemind(None).choreo.get_num_bots()
    #     print('[RLBotChoreography]: Using the number of bots provided by the chosen choreography.')
    # except NotImplementedError:
    #     num_bots = arguments['--num-bots']
    #     print('[RLBotChoreography]: Using default or given number of bots.')
    # finally:
    #     min_bots = min(int(num_bots), MAX_PLAYERS)

    # TODO Access GUI info somehow

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
    for i in range(max(len(bundles), min_bots)): # FIXME
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
    # Waits until a START command is received.
    while queue.get() != QCommand.START:
        continue
    
    setup_match()

    while True:
        # TODO Get info from GUI and tell hivemind what obj to use.
        # Maybe like this: hivemind.Hivemind(queue, obj_from_gui()) ?
        my_hivemind = hivemind.Hivemind(queue)
        my_hivemind.start() # Loop only quits on STOP command.

        # Reloads hivemind for new changes to take place.
        reload(hivemind)
        
        # Checks what to do after hivemind died.
        command = queue.get()

        if command == QCommand.ALL:
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
            __import__(module)

            # Finds the classes in the module.
            classes = inspect.getmembers(sys.modules[module], inspect.isclass)
            for name, obj in classes:
                # Checks whether the class subclasses Choreography.
                if issubclass(obj, Choreography) and obj is not Choreography:
                    # FIXME Watch out for name conflicts!
                    choreographies[name] = {'module': module, 'obj': obj} # TODO Might not need to save which module it came from?

        return choreographies

    def start():
        print("[RLBotChoreography]: Starting up!")
        queue.put(QCommand.START)
        button_start.destroy() # Removes the button so we cannot start again.

    def choreo_selected(var):
        """
        Updates the bot number entry box with the given number in the choreography (if there is one).
        """
        try:
            num_bots = choreographies[var]['obj'].get_num_bots()
        except NotImplementedError:
            num_bots = 10
        finally:
            min_bots = min(int(num_bots), MAX_PLAYERS)

        entry_num_bots.delete(0, last=tk.END)
        entry_num_bots.insert(0, min_bots)

    def reload_hive():
        print("[RLBotChoreography]: Stopping Hivemind.")
        queue.put(QCommand.STOP)
        # Reloading just the Hivemind.
        queue.put(QCommand.HIVE)

    def reload_all():
        print("[RLBotChoreography]: Stopping Hivemind.")
        queue.put(QCommand.STOP)
        print("[RLBotChoreography]: Reloading all.")
        queue.put(QCommand.ALL)

    # TODO Make GUI look better.

    root = tk.Tk()
    frame = tk.Frame(root)
    frame.pack()

    # Start button.
    button_start = tk.Button(frame, text="Start", command=start)
    button_start.pack()

    # Hive reset button.
    button_reload_hive = tk.Button(frame, text="↻ Hivemind", command=reload_hive)
    button_reload_hive.pack()
        
    # All reset button.
    button_reload_all = tk.Button(frame, text="↻ All", command=reload_all)
    button_reload_all.pack()

    # Dropdown menu.
    choreographies = find_choreographies()
    menuvar = tk.StringVar(root)
    menuvar.set('LightfallChoreography') # set the default option
    dropMenu = tk.OptionMenu(frame, menuvar, *choreographies, command=choreo_selected)
    dropMenu.pack()

    label_num_bots = tk.Label(frame, text="Number of bots")
    label_num_bots.pack()

    entry_num_bots = tk.Entry(frame)
    entry_num_bots.pack()
    entry_num_bots.insert(0, 10)

    root.mainloop()

class QCommand:
    START = 0
    STOP = 1
    HIVE = 2
    ALL = 3

if __name__ == '__main__':

    # Runs GUI and Hivemind on two different threads.
    q = Queue()
    thread1 = Thread(target=run_gui, args=(q, ))
    thread1.start()  
    thread2 = Thread(target=run_RLBotChoreography, args=(q, ))
    thread2.start()
    q.join()
