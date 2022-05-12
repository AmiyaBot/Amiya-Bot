import os

from core.database.user import OperatorBox
from core.builtin.imageCreator import ImageElem, create_image
from core.resource.arknightsGameData import ArknightsGameData, Operator


def get_user_box(user_id):
    box: OperatorBox = OperatorBox.get_or_none(user_id=user_id)

    if not box or not box.operator:
        return '博士，您尚未获得任何干员'

    operators = ArknightsGameData().operators

    collect = {
        6: [],
        5: [],
        4: [],
        3: []
    }
    images = []

    for item in box.operator.split('|'):
        operator_name, rarity, count = tuple(item.split(':'))

        if operator_name in operators:
            operator: Operator = operators[operator_name]

            if operator.rarity in collect:
                collect[operator.rarity].append(
                    {
                        'avatar': f'resource/gamedata/avatar/{operator.id}.png',
                        'rank': f'resource/images/rank/{count if int(count) <= 6 else 6}.png'
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
    box: OperatorBox = OperatorBox.get_or_none(user_id=user_id)

    if not box:
        return None

    count = 0
    rarity = {
        3: [0, 0],
        4: [0, 0],
        5: [0, 0],
        6: [0, 0]
    }
    operators = box.operator.split('|')
    box_num = len(operators)

    for item in operators:
        _, r, c = tuple(item.split(':'))

        rarity[int(r)][0] += 1
        rarity[int(r)][1] += int(c)

        count += int(c)

    def rate(n):
        return f'{round(rarity[n][1] / count * 100, 2) if rarity[n][1] else 0}%'

    return {
        'box_num': box_num,
        'count': count,
        'rarity_6': (rarity[6][0], rate(6)),
        'rarity_5': (rarity[5][0], rate(5)),
        'rarity_4': (rarity[4][0], rate(4)),
        'rarity_3': (rarity[3][0], rate(3))
    }
