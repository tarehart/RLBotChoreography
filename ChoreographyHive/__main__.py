"""RLBotChoreography

Usage:
    ChoreographyHive [--bot-folder=<folder>]
    ChoreographyHive (-h | --help)

Options:
    -h --help               Shows this help message.
    --bot-folder=<folder>   Searches this folder for bot configs to use for names and appearances [default: .].
"""
import glob
import inspect
import os
import sys
from importlib import reload, import_module
from os.path import dirname, basename, isfile, join
from queue import Queue
from threading import Thread

from docopt import docopt
from rlbot.matchconfig.conversions import parse_match_config
from rlbot.matchconfig.match_config import PlayerConfig
from rlbot.parsing.agent_config_parser import load_bot_appearance
from rlbot.parsing.directory_scanner import scan_directory_for_bot_configs
from rlbot.parsing.rlbot_config_parser import create_bot_config_layout
from rlbot.setup_manager import SetupManager
from rlbot.utils.structures.start_match_structures import MAX_PLAYERS

import hivemind
from choreography.choreography import Choreography
from queue_commands import QCommand


# TODO:
# - Do bot-folder from inside the GUI
# - Prettify GUI
class RLBotChoreography:

    def __init__(self):
        # Runs GUI and Hivemind on two different threads.
        q = Queue()
        thread1 = Thread(target=self.run_gui, args=(q, ))
        thread1.start()
        thread2 = Thread(target=self.run_RLBotChoreography, args=(q, ))
        thread2.start()
        q.join()


    def setup_match(self):
        # TODO This should be replaced?
        arguments = docopt(__doc__)

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
        for i in range(max(len(bundles), self.min_bots)):
            copied = PlayerConfig()
            copied.bot = player_config.bot
            copied.name = player_config.name
            copied.rlbot_controlled = player_config.rlbot_controlled
            copied.config_path = player_config.config_path
            copied.team = player_config.team
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


    def run_RLBotChoreography(self, queue):
        """
        If Hivemind breaks out of game_loop it is reloaded and recreated.
        """
        # Waits until a START command is received.
        while queue.get() != QCommand.START:
            continue

        self.setup_match()

        while True:
            my_hivemind = hivemind.Hivemind(queue, self.choreo_obj)
            my_hivemind.start() # Loop only quits on STOP command.

            # Reloads hivemind for new changes to take place.
            # reload(sys.modules[self.choreo_obj.__module__])
            reload(hivemind)

            # Checks what to do after Hivemind died.
            command = queue.get()
            if command == QCommand.ALL:
                self.setup_match()
            elif command == QCommand.EXIT:
                break

        exit() # Clean exit.


    def run_gui(self, queue):
        """
        Runs the simple gui.
        """

        def reload_choreographies():
            """
            Finds and reloads all choreo modules and puts the found choreographies inside a dictionary.
            """
            # Automatically finds all choreo modules.
            modules = glob.glob(join(dirname(__file__), "choreography/choreos/*.py"))
            choreo_modules = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

            choreographies = {}
            for choreo in choreo_modules:
                module = f'choreography.choreos.{choreo}'

                # Try reloading the module.
                try:
                    reload(sys.modules[module])
                    classes = inspect.getmembers(sys.modules[module], inspect.isclass)

                # If not loaded yet, import it.
                except:
                    print(f'Module not found, importing {module}')
                    import_module(module)
                    classes = inspect.getmembers(sys.modules[module], inspect.isclass)

                # Find all the choreography classes inside.
                finally:
                    for name, obj in classes:
                        # Checks whether the class subclasses Choreography.
                        if issubclass(obj, Choreography) and obj is not Choreography:
                            # FIXME Watch out for name conflicts!
                            choreographies[name] = obj

            return choreographies

        def start():
            num_bots_changed()
            print("[RLBotChoreography]: Starting up!")
            queue.put(QCommand.START)

            # Removes the button so we cannot start again.
            button_start.destroy()

            # Hive reset button.
            button_reload_hive = tk.Button(frame, text="↻ Hivemind", command=reload_hive)
            button_reload_hive.pack()

            # All reset button.
            button_reload_all = tk.Button(frame, text="↻ All", command=reload_all)
            button_reload_all.pack()

        def num_bots_changed():
            """
            Looks at the choreography's requested number of bots and uses that. Otherwise will use the entered number.
            """
            try:
                num_bots = self.choreo_obj.get_num_bots()
            except NotImplementedError:
                num_bots = int(entry_num_bots.get())
            finally:
                self.min_bots = min(int(num_bots), MAX_PLAYERS)
                entry_num_bots.delete(0, last=tk.END)
                entry_num_bots.insert(0, self.min_bots)

        def choreo_selected(var):
            """
            Updates the selected choreography.
            """
            self.choreographies = reload_choreographies()
            self.choreo_obj = self.choreographies[var]
            num_bots_changed()

        def reload_hive():
            num_bots_changed()
            print("[RLBotChoreography]: Stopping Hivemind.")
            queue.put(QCommand.STOP)
            choreo_selected(menuvar.get())
            print("[RLBotChoreography]: Reloading Hivemind.")
            queue.put(QCommand.HIVE)

        def reload_all():
            num_bots_changed()
            print("[RLBotChoreography]: Stopping Hivemind.")
            queue.put(QCommand.STOP)
            choreo_selected(menuvar.get())
            print("[RLBotChoreography]: Reloading all.")
            queue.put(QCommand.ALL)

        # TODO Make GUI look better.
        import tkinter as tk

        root = tk.Tk()
        frame = tk.Frame(root)
        frame.pack()

        # Start button.
        button_start = tk.Button(frame, text="Start", command=start)
        button_start.pack()

        # Dropdown menu.
        self.choreographies = reload_choreographies()
        menuvar = tk.StringVar(root)
        menuvar.set('LightfallChoreography') # Set the default option
        dropMenu = tk.OptionMenu(frame, menuvar, *self.choreographies, command=choreo_selected)
        dropMenu.pack()

        # Label for the entry box.
        label_num_bots = tk.Label(frame, text="Number of bots")
        label_num_bots.pack()

        # Number of bots entry box.
        entry_num_bots = tk.Entry(frame)
        entry_num_bots.insert(0, 10)
        entry_num_bots.pack()

        # This is here just to make sure everything is set up by default.
        choreo_selected(menuvar.get())

        root.mainloop()

        # Clean exit.
        print('[RLBotChoreography]: Shutting down.')
        queue.put(QCommand.STOP)
        queue.put(QCommand.EXIT)
        exit()


if __name__ == '__main__':
    # Starts the show :)
    RLBotChoreography()
