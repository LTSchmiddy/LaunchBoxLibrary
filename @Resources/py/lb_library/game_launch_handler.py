import os, subprocess, webbrowser
import xml.etree.ElementTree as ET
from . import launch_handlers

handlers = sorted([i() for i in launch_handlers.LauncherHandlerBase.__subclasses__()], key=lambda x: x.priority, reverse=True)

def handle_game_launch(game: ET.Element):
    global handlers
    print(f"Lauching {game.find('Title').text}...")
    
    for i in handlers:
        i.set_game(game)
        
        if i.check():
            print(f"Using launcher: '{type(i).__name__}'...")
            i.launch()
            break


