import time
from os import system
import sys

#Don't make fun of me 😡😡😡

def restart():
    time.sleep(10)
    if sys.platform == 'linux':
        system(f"gnome-terminal --command 'python3.7 core.py'")
    else:
        system("start core.py")

restart()
