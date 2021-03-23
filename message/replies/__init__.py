from functions.functionsIndex import FunctionsIndex
from database.baseController import BaseController

from .admin import admin
from .emotion import emotion
from .waiting import waiting
from .greeting import greeting
from .faceImage import face_image
from .adminForGroup import group_admin
from .nlp import natural_language_processing

function = FunctionsIndex()
database = BaseController()


def reply_func_list(data):
    replies = [
        {
            # 等待事件
            'func': waiting,
            'need_call': False
        }
    ]

    group_admin_func = {
        # 群管功能
        'func': group_admin,
        'need_call': True
    }

    if data['type'] == 'group':

        group_status = database.group.get_status(data['group_id'])
        if group_status and group_status['active'] == 0:
            return [group_admin_func]

        replies.append(group_admin_func)
        replies += [
            {
                # 打招呼
                'func': greeting,
                'need_call': False
            },
            {
                # 表情包
                'func': face_image,
                'need_call': True
            },
            {
                # 信赖事件
                'func': emotion,
                'need_call': True
            },
            {
                # 使用功能
                'func': function.action,
                'need_call': True,
                'without_call': True
            },
            {
                # 自然语言处理
                'func': natural_language_processing,
                'need_call': True
            }
        ]
    else:
        replies += [
            {
                # 管理员指令
                'func': admin,
                'need_call': False
            }
        ]

    return replies
