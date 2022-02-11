from core.database.user import *


@table
class UserBox(UserBaseModel):
    user_id: str = TextField()
    operator_name: str = TextField()
    rarity: int = IntegerField()
    count: int = IntegerField(default=1)


def get_user_box(user_id):
    box: List[UserBox] = UserBox.select().where(UserBox.user_id == user_id)


def get_user_gacha_detail(user_id):
    box: List[UserBox] = UserBox.select().where(UserBox.user_id == user_id)

    count = 0
    raritys = {
        3: [0, 0],
        4: [0, 0],
        5: [0, 0],
        6: [0, 0]
    }
    box_num = len(box)

    for item in box:
        raritys[item.rarity][0] += 1
        raritys[item.rarity][1] += item.count

        count += item.count

    def rate(n):
        return f'{round(raritys[n][1] / count * 100, 2) if raritys[n][1] else 0}%'

    return {
        'box_num': box_num,
        'count': count,
        'raritys_6': (raritys[6][0], rate(6)),
        'raritys_5': (raritys[5][0], rate(5)),
        'raritys_4': (raritys[4][0], rate(4)),
        'raritys_3': (raritys[3][0], rate(3))
    }
