from modules.gameData import GameData
from database.baseController import BaseController

if __name__ == '__main__':
    BaseController().material.truncate_all()
    GameData().update_operators()
    GameData().update_stage()
