import webbrowser
import xml.etree.ElementTree as ET
from . import LauncherHandlerBase

class EpicLauncher(LauncherHandlerBase):
    priority = 5
    
    def check(self) -> bool:
        return self.app_path.startswith("com.epicgames.launcher://")
    
    def launch(self):
        webbrowser.open(self.app_path)
 
        
class SteamLauncher(LauncherHandlerBase):
    priority = 10
    
    def check(self) -> bool:
        return self.app_path.startswith("steam://")
    
    def launch(self):
        webbrowser.open(self.app_path)
        
__all__ = ('EpicLauncher', 'SteamLauncher')