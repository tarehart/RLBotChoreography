import sys
from importlib import reload, import_module

import tkinter as tk 

my_module = import_module('example')
my_class = my_module.MyClass # This is not reloaded!

def reload_example():
    global my_class 
    print('reloading {sys.modules[instance.__module__]}')
    reload(sys.modules[my_class.__module__])
    my_class = my_module.MyClass # THIS NEEDS TO BE DONE IN RLBOTCHOREOGRAPHY

def print_statement():
    print(my_class().statement)

root = tk.Tk()
frame = tk.Frame(root)
frame.pack()

# Reload button.
reload_button = tk.Button(frame, text="Reload", command=reload_example)
reload_button.pack()

# Print button.
print_button = tk.Button(frame, text="Print", command=print_statement)
print_button.pack()

root.mainloop()