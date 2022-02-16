import os

from core.database.user import *
from core.builtin.imageCreator import ImageElem, create_image
from core.resource.arknightsGameData import ArknightsGameData, Operator


@table
class UserBox(UserBaseModel):
    user_id: str = TextField()
    operator_name: str = TextField()
    rarity: int = IntegerField()
    count: int = IntegerField(default=1)


def get_user_box(user_id):
    box: List[UserBox] = UserBox.select().where(UserBox.user_id == user_id)

    operators = ArknightsGameData().operators

    collect = {
        6: [],
        5: [],
        4: [],
        3: []
    }
    images = []

    for item in box:
        if item.operator_name in operators:
            operator: Operator = operators[item.operator_name]

            if operator.rarity in collect:
                collect[operator.rarity].append(
                    {
                        'avatar': f'resource/images/avatar/{operator.id}.png',
                        'rank': f'resource/images/rank/{item.count if item.count <= 6 else 6}.png'
                    }
                )

    size = 60
    rank = 20
    padding = 10

    y_pos = 26 - size
    max_length = 10
    for rarity, items in collect.items():
        x_pos = padding
        y_pos += size + 10

        for index, item in enumerate(items):
            if os.path.exists(item['avatar']):
                images.append(ImageElem(
                    path=item['avatar'],
                    pos=(x_pos, y_pos),
                    size=size
                ))
                images.append(ImageElem(
                    path=item['rank'],
                    pos=(x_pos + size - rank, y_pos + size - rank),
                    size=rank
                ))

            if (index + 1) % max_length == 0:
                x_pos = padding
                y_pos += size
            else:
                x_pos += size

    return create_image(text='博士，这是您的干员列表（按获取顺序）',
                        width=size * max_length + padding * 2,
                        height=y_pos + padding + size,
                        images=images,
                        padding=padding,
                        bgcolor='#F5F5F5')


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
