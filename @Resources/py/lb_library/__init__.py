from __future__ import annotations

import sys, os, pathlib, sched, time, threading, subprocess
from datetime import datetime, timezone, timedelta
# from collections import namedtuple
from typing import NamedTuple
import xml.etree.ElementTree as ET

from fuzzywuzzy import fuzz
from dateutil import tz
import pytz
from pytz import tzinfo
import tzlocal

from PythonLoaderUtils.meaure_type import MeasureBase
from PythonLoaderUtils.monitor_types import MonitorBase
from PythonLoaderUtils.rm_stub import RainmeterW

from .recent_game_list_layout import generate_layout
from .game_launch_handler import handle_game_launch

# Replace this with a RM variable later...
LB_Root = pathlib.Path("C:/Users/thewi/LaunchBox")
LB_Platforms_Folder = pathlib.Path("C:/Users/thewi/LaunchBox/Data/Platforms")
LB_Platforms_Info = pathlib.Path("C:/Users/thewi/LaunchBox/Data/Platforms.xml")

name_cover_match = 90

allowed_cover_types = [
    'Box - Front',
    'Box - Front - Reconstructed',
    'Epic Games Poster'
]

def xml_to_datetime(dtstr: str) -> datetime:
    # print(f"{dtstr[20:27]=}")
    # print(f"UTC{dtstr[27:33]}")
    
    offset_hrs = int(dtstr[27:30])
    offset_min = int(dtstr[31:33])
    
    zone = tz.tzoffset(f"{dtstr[27:33]}", offset_hrs * 3600 + offset_min * 60)
    
    return datetime(
        year=int(dtstr[:4]),
        month=int(dtstr[5:7]),
        day=int(dtstr[8:10]),
        hour=int(dtstr[11:13]),
        minute=int(dtstr[14:16]),
        second=int(dtstr[17:19]),
        # microsecond=int(dtstr[20:27]), # Having some issues with handling the microseconds. We'll ignore for now.
        tzinfo=zone
    )
    
def current_datetime_as_xml() -> str:
    dt = datetime.now()
    zone = tzlocal.get_localzone()
    
    offset: timedelta = zone.utcoffset(dt)
    sec = offset.seconds
    
    min = sec // 60
    sec = sec % 60
    
    hrs = min // 60
    min = min % 60
    
    hrs = offset.days*24 + hrs

    # Having some issues with handling the microseconds. We'll ignore for now.
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.0000000{'+' if hrs >= 0 else '-'}{abs(hrs):02d}:{min:02d}"

class PlatformFileRef(NamedTuple):
    platform: str
    path: str
    tree: ET.ElementTree

class CoverCandidate(NamedTuple):
    ratio: int
    path: str

class GameEntry(NamedTuple):
    last_played: datetime
    entry: ET.Element
    cover_image: str

class RecentGamesMonitor(MonitorBase):
    update_sched: sched.scheduler
    update_event: sched.Event
    update_interval: int = 300
    
    games: list[GameEntry]
    platforms_info: ET.ElementTree
    platforms: dict[str, PlatformFileRef]
    refresh_thread: threading.Thread
    
    tree_lock: threading.Lock
    
    @classmethod
    def get_instance(cls) -> RecentGamesMonitor:
        return super().get_instance()
    
    
    def __init__(self):
        super().__init__()
        self.update_sched = sched.scheduler(time.time, time.sleep)
        self.update_event = None   
        self.games = []
        self.platforms_info = ET.parse(str(LB_Platforms_Info))
        self.platforms = {}
        self.refresh_thread = None
        
        self.tree_lock = threading.Lock()
        
        # self.refresh_games()
        self.on_update()
        
    
    def refresh_games_threaded(self):
        self.refresh_thread = threading.Thread(None, self.refresh_games(), daemon=True)
        self.refresh_thread.start()
        
    def refresh_games(self):
        # Don't want the launcher to change data while we're trying to scan it:
        with self.tree_lock:
            self.games = []
            self.platforms_info = ET.parse(str(LB_Platforms_Info))
            for i in os.listdir(LB_Platforms_Folder):
                self.process_platform(LB_Platforms_Folder.joinpath(i))
            
            self.games.sort(key=lambda x: x.last_played, reverse=True)

    
    
    def process_platform(self, path: pathlib.Path):
        tree = ET.parse(str(path))
        platform_name = path.name.removesuffix(".xml")
        
        # We'll want to hold on to these tree objects, in case we need to update the files (when launching a game, for example).
        self.platforms[platform_name] = PlatformFileRef(platform=platform_name, path=path, tree=tree)
        
        games = tree.getroot().findall("Game")
        for i in games:

            lp = i.find("LastPlayedDate")
            if lp is not None:
                self.process_game(i, platform_name)

    def process_game(self, game: ET.Element, platform_name: str):
        lpd = xml_to_datetime(game.find("LastPlayedDate").text)
        # print(f"{current_datetime_as_xml()}")
        
        self.find_cover_image(game, platform_name)
        
        retVal = GameEntry(last_played=lpd, entry=game, cover_image=self.find_cover_image(game, platform_name))
        # print(retVal)
        self.games.append(retVal)
        
        
    def find_cover_image(self, game: ET.Element, platform_name: str):
        cover: CoverCandidate = None
        
        for i in self.platforms_info.getroot().findall("PlatformFolder"):
            if i.find("Platform").text == platform_name and i.find("MediaType").text in allowed_cover_types:
                # print(i.find("FolderPath").text)
                fullpath = LB_Root.joinpath(i.find("FolderPath").text)
                
                cover = self.scan_folder_for_cover(fullpath, game.find('Title').text, cover)
        
        return cover.path
        # print(game.find('Title').text, cover.path)
    
    def scan_folder_for_cover(self, path: pathlib.Path, name: str, candidate: CoverCandidate = None):
        for i in os.listdir(path):
            fullpath = path.joinpath(i)
            
            if fullpath.is_dir():
                candidate = self.scan_folder_for_cover(fullpath, name, candidate)
            elif fullpath.is_file():
                new_candidate = CoverCandidate(fuzz.ratio(name, i.split('.')[0]), fullpath)
                if candidate is None or candidate.ratio <= new_candidate.ratio:
                    candidate = new_candidate
                    # print(f"{candidate.ratio}")

        return candidate
    

    
    def launch_game(self, index: int):
        with self.tree_lock:
            if index >= len(self.games):
                print("Index '{index}' too high. No game selected.")
                return
                
            game = self.games[index]
            
            # Updating metadata.
            count = int(game.entry.find("PlayCount").text) + 1
            game.entry.find("PlayCount").text = str(count)
            game.entry.find("LastPlayedDate").text = current_datetime_as_xml()
            
            # Writing updated metadata to LaunchBox's XML files.
            platform = self.platforms[game.entry.find("Platform").text]
            platform.tree.write(platform.path)
            
            handle_game_launch(game.entry)
        
        self.refresh_games_threaded()
        
        
    def on_update(self):
        if self.refresh_thread is not None and self.refresh_thread.is_alive():
            print("Last 'refresh_games()' is still running.")
        else:
            self.refresh_games_threaded()
            
        self.update_event = self.update_sched.enter(self.update_interval, 1, self.on_update)
    
    def update(self):
        # pass
        if not self.update_sched.empty():
            self.update_sched.run(blocking=False)
        
    def shutdown(self):
        if not self.update_sched.empty():
            self.update_sched.cancel(self.update_event)
        
        super().shutdown()


class RecentGamesNameMeasure(MeasureBase):
    recent_pos: int = 0
    game_name: str = ""
    
    def __init__(self):
        super().__init__()
        RecentGamesMonitor.increase_accessors()
        # RecentGamesMonitor.get_instance().refresh_games()
    
    def Reload(self, rm: RainmeterW, maxValue):
        super().Reload(rm, maxValue)
        self.recent_pos = rm.RmReadInt("RecentEntry", 0)
        
        
    def Update(self):
        RecentGamesMonitor.get_instance().update()
        if (len(RecentGamesMonitor.get_instance().games) > self.recent_pos):
            self.game_name = RecentGamesMonitor.get_instance().games[self.recent_pos].entry.find("Title").text
        else:
            self.game_name = None
        return 0.0
        
        
    def GetString(self):
        return self.game_name
    
    def ExecuteBang(self, args):
        return super().ExecuteBang(args)
    
    def Finalize(self):
        super().Finalize()
        RecentGamesMonitor.decrease_accessors()


class RecentGamesCountMeasure(MeasureBase):
    recent_pos: int = 0
    game_count: float = 0.0
    
    def __init__(self):
        super().__init__()
        RecentGamesMonitor.increase_accessors()
        # RecentGamesMonitor.get_instance().refresh_games()
    
    def Reload(self, rm: RainmeterW, maxValue):
        super().Reload(rm, maxValue)
        self.recent_pos = rm.RmReadInt("RecentEntry", 0)
        
        
    def Update(self):
        RecentGamesMonitor.get_instance().update()
        if (len(RecentGamesMonitor.get_instance().games) > self.recent_pos):
            self.game_count = float(RecentGamesMonitor.get_instance().games[self.recent_pos].entry.find("PlayCount").text)
        else:
            self.game_count = 0
        
        
        
    def GetString(self):
        return str(int(self.game_count))
    
    def ExecuteBang(self, args):
        return super().ExecuteBang(args)
    
    def Finalize(self):
        super().Finalize()
        RecentGamesMonitor.decrease_accessors()

class RecentGamesArtMeasure(MeasureBase):
    recent_pos: int = 0
    game_cover: str = ""
    
    def __init__(self):
        super().__init__()
        RecentGamesMonitor.increase_accessors()
        # RecentGamesMonitor.get_instance().refresh_games()
    
    def Reload(self, rm: RainmeterW, maxValue):
        super().Reload(rm, maxValue)
        self.recent_pos = rm.RmReadInt("RecentEntry", 0)
        
        
    def Update(self):
        RecentGamesMonitor.get_instance().update()
        if (len(RecentGamesMonitor.get_instance().games) > self.recent_pos):
            self.game_cover = RecentGamesMonitor.get_instance().games[self.recent_pos].cover_image
        else:
            self.game_cover = ""
        
    def GetString(self):
        return str(self.game_cover)
    
    def ExecuteBang(self, args):
        return super().ExecuteBang(args)
    
    def Finalize(self):
        super().Finalize()
        RecentGamesMonitor.decrease_accessors()


class RecentGamesDynamicInc(MeasureBase):
    NumEntries: int
    should_refresh: bool
    
    
    def __init__(self):
        super().__init__()
        self.should_refresh = False
    
    def Reload(self, rm: RainmeterW, maxValue):
        super().Reload(rm, maxValue)
        self.NumEntries = rm.RmReadInt("NumEntries", 5)
        
        if self.should_refresh:
            self.should_refresh = False
            self.last_rm.RmExecute('!Refresh')
        
        
    def Update(self):
        return 0.0
        
    def GetString(self):
        return ""
    
    def ExecuteBang(self, args: str):
        super().ExecuteBang(args)
        
        if args.lower() == "regen":
            generate_layout(self.NumEntries)
            self.should_refresh = True
        else:
            print(f"Unknown bang param: {args}")
    
    def Finalize(self):
        super().Finalize()


class RecentGamesLaunch(MeasureBase):
    should_refresh: bool
    
    def __init__(self):
        self.should_refresh = False
        super().__init__()
        RecentGamesMonitor.increase_accessors()
        # RecentGamesMonitor.get_instance().refresh_games()
    
    def Reload(self, rm: RainmeterW, maxValue):
        super().Reload(rm, maxValue)
        self.recent_pos = rm.RmReadInt("RecentEntry", 0)
        
        # if self.should_refresh:
        #     self.should_refresh = False
        #     self.last_rm.RmExecute('!Refresh')
        
    def Update(self):
        if self.should_refresh:
            self.should_refresh = False
            self.last_rm.RmExecute('!Refresh')

        return 0.0
        
    def GetString(self):
        return ""
    
    def ExecuteBang(self, args: str):
        super().ExecuteBang(args)

        RecentGamesMonitor.get_instance().launch_game(int(args))
        # self.should_refresh = True
    
    def Finalize(self):
        super().Finalize()
