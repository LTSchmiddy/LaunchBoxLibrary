import xml.etree.ElementTree as ET

class LauncherHandlerBase:
    priority: int = 0
    
    game: ET.Element = None
    
    def set_game(self, game: ET.Element):
        self.game = game
    
    
    # Helper attributes for the subclasses
    @property
    def app_path(self):
        return self.game.find('ApplicationPath').text
    
    @property
    def emulator(self):
        return self.game.find('Emulator').text       
    
    @property
    def cmd(self):
        return self.game.find('CommandLine').text
    
    # These are meant to be implemented by subclasses
    def check(self) -> bool:
        return False
    
    def launch(self):
        pass
    

from .protocol_launchers import *
from .executable_launchers import *
from .emulation_launchers import *