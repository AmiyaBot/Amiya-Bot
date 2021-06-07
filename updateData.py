from modules.dataSource.gameData import GameData

if __name__ == '__main__':
    game = GameData(network=True)
    game.update(cache=False)
