import subprocess, os
import xml.etree.ElementTree as ET
from . import LauncherHandlerBase

class GeneralEmulatorLauncher(LauncherHandlerBase):
    priority = 15
    
    def check(self) -> bool:
        return self.emulator is not None
    
    def launch(self):
        print("Uses Emulator. Currently unsure how to launch this game...")
        
