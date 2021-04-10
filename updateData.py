from modules.gameData import GameData
from database.baseController import BaseController

if __name__ == '__main__':
    BaseController().material.truncate_all()
    GameData().update_operators()
    GameData().update_materials()
    GameData().update_stage()
    print('全部数据更新完毕')
