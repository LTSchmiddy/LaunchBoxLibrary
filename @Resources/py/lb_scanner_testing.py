import sys, os, pathlib
from datetime import timezone, datetime
import xml.etree.ElementTree as ET

# Config:
# LB_Platforms_Folder = pathlib.Path("C:/Users/thewi/LaunchBox/Data/Platforms")

from lb_library import *

if __name__ == '__main__':
    RecentGamesMonitor.increase_accessors()
    RecentGamesMonitor.get_instance().refresh_games()
    print(RecentGamesMonitor.get_instance().games)
    RecentGamesMonitor.decrease_accessors()
