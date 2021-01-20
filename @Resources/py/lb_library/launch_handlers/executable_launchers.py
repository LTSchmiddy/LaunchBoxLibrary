import subprocess, os
import xml.etree.ElementTree as ET
from . import LauncherHandlerBase

class ExecutableLauncher(LauncherHandlerBase):
    priority = 0
    
    def check(self) -> bool:
        return self.app_path.endswith(".exe") or self.app_path.endswith(".bat")
    
    def launch(self):
        subprocess.Popen(
            f"\"{self.app_path}\" {self.cmd if self.cmd is not None else ''}",
            cwd=os.path.dirname(self.app_path),
            close_fds=True
        )
 
        
