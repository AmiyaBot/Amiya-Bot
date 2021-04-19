import time

from modules.gameData import GameData
from modules.commonMethods import calc_time_total

if __name__ == '__main__':
    print('即将在 5 秒后开始全量更新', end='', flush=False)
    sec = 5
    while sec > 0:
        sec -= 1
        print('.', end='' if sec > 0 else '\n', flush=True)
        time.sleep(1)

    start = int(time.time())
    game = GameData()
    game.update_operators(refresh=True)
    game.update_materials(refresh=True)
    game.update_stage()
    print('全部数据更新完毕，总耗时%s' % calc_time_total(int(time.time()) - start))
