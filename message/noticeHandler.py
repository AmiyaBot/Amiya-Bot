import os
import time
import json

from database.baseController import BaseController
from modules.network.httpRequests import HttpRequests

database = BaseController()


class NoticeHandler(HttpRequests):
    def __init__(self):
        super().__init__()

    def on_notice(self, message):

        notice_type = message['type']

        print('[%s][%s]' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), notice_type))

        try:
            if os.path.exists('remind') is False:
                os.mkdir('remind')
            with open('remind/%s.json' % notice_type, mode='w+') as remind:
                remind.write(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            print(e)

        if notice_type == 'BotMuteEvent':
            self.leave_group(message['operator']['group']['id'])

        if notice_type == 'MemberJoinEvent':
            self.send_group_message({
                'user_id': message['member']['id'],
                'group_id': message['member']['group']['id']
            }, message='欢迎%s' % message['member']['memberName'], at=True)

        if notice_type == 'BotJoinGroupEvent':
            self.send_group_message({
                'group_id': message['group']['id']
            }, message='博士，初次见面，这里是阿米娅2号，姐姐去了很远的地方，今后就由我来代替姐姐的工作吧，请多多指教哦')
            database.group.record_group(message['group']['id'])

        if notice_type == 'BotLeaveEventActive':
            self.leave_group(message['group']['id'], False)

        if notice_type == 'BotInvitedJoinGroupRequestEvent':
            groups = database.group.get_all_group()
            self.handle_join_group(message, len(groups) >= 150)
