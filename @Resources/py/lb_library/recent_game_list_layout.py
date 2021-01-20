import os, pathlib

from configparser import ConfigParser

def generate_layout(
    game_count: int = 5,
    subpath: str = "recent_games_view", 
):
    cfg: ConfigParser = ConfigParser()
    
    
    def buildPosX(var: str, index: int):
        return f"(#offsetX# + #entryW# * {index} + #spacingW# * {index} + #{var}#)"
    
    def buildPosY(var: str):
        return f"(#offsetY# + #{var}#)"
    
    
    def generate_game_slot(cfg: ConfigParser, index: int) -> dict: 
        cfg[f"meterGameBox{index}"] = {
            "Meter": "Shape",
            "LeftMouseUpAction": f'[!CommandMeasure "#onClickMeasure#" "{index}"]',
            "Shape": f"Rectangle (#offsetX# + #entryW# * {index} + #spacingW# * {index}),(#offsetY# + #textCoverH#)," \
                "#entryW#,(#entryH# - #textCoverH#) | Fill Color 0,0,0,255 | StrokeWidth 2 | Stroke Color 255,255,255,50"  
        }
              
        cfg[f"measureGameArt{index}"] = {
            "Measure": "Plugin",
            "Plugin": "PyPlugin",
            "Info": "#@#py/mod_info.json",
            "Loader": "RecentGamesArtMeasure()",
            "RecentEntry": index,
            "UpdateDivider": 1
        }
        
        cfg[f"meterGameArt{index}"] = {
            "Meter": "Image",
            "MeasureName": f"measureGameArt{index}",
            "ImageName": f"[measureGameArt{index}]",
            "W": "#gameImageW#",
            "H": "#gameImageH#",
            "X": buildPosX("gameImageX", i),
            "Y": buildPosY("gameImageY"),
            # "Text": "%1",    
        }
        
        cfg[f"measureGameName{index}"] = {
            "Measure": "Plugin",
            "Plugin": "PyPlugin",
            "Info": "#@#py/mod_info.json",
            "Loader": "RecentGamesNameMeasure()",
            "RecentEntry": index,
            "UpdateDivider": 1
        }
        
        cfg[f"meterGameName{index}"] = {
            "Meter": "String",
            "MeterStyle": "#GameNameStyle#",
            "MeasureName": f"measureGameName{index}",
            "W": "#gameNameW#",
            "H": "#gameNameH#",
            "X": buildPosX("gameNameX", i),
            "Y": buildPosY("gameNameY"),
            # "Text": "%1",    
        }
        
        # cfg[f"measureGameCount{index}"] = {
        #     "Measure": "Plugin",
        #     "Plugin": "PyPlugin",
        #     "Info": "#@#py/mod_info.json",
        #     "Loader": "RecentGamesCountMeasure()",
        #     "RecentEntry": index,
        #     "UpdateDivider": 1
        # }
        
        # cfg[f"meterGameCount{index}"] = {
        #     "Meter": "String",
        #     "MeterStyle": "#GameCountStyle#",
        #     "MeasureCount": f"measureGameCount{index}",
        #     "W": "#gameCountW#",
        #     "H": "#gameCountH#",
        #     "X": buildPosX("gameCountX", i),
        #     "Y": buildPosY("gameCountY",),
        #     # "Text": "%1",    
        # }
    
    
    
    for i in range (0, game_count):
        generate_game_slot(cfg, i)
        
    cfg[f"Variables"] = {
        "totalW": f"(#offsetX# + #entryW# * {game_count} + #spacingW# * {game_count})",
        "totalH": f"(#offsetY# + #entryH# + #spacingH#)"
        # "Text": "%1",    
    }
    
    cfg_file = open(pathlib.Path("dynamic_inc").joinpath(subpath+".inc"), 'w')
    cfg.write(cfg_file)
    cfg_file.close()

if __name__ == '__main__':
    generate_layout(6, "recent_games_view")