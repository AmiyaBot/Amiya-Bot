import os
import time
import json

from modules.network.httpRequests import HttpRequests


class EventsHandler(HttpRequests):
    def __init__(self):
        super().__init__()

    def on_events(self, message):

        events_type = message['type']

        print('[%s][%s]' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), events_type))

        try:
            if os.path.exists('remind') is False:
                os.mkdir('remind')
            with open('remind/%s.json' % events_type, mode='w+', encoding='utf-8') as remind:
                remind.write(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            print('Remind2', e)

        if events_type == 'MemberJoinEvent':
            self.send_message(
                data={
                    'type': 'group',
                    'user_id': message['member']['id'],
                    'group_id': message['member']['group']['id']
                },
                message='欢迎新博士%s~，我是阿米娅，请多多指教哦' % message['member']['memberName'],
                at=True
            )

        if events_type == 'BotJoinGroupEvent':
            self.send_message(
                data={
                    'type': 'group',
                    'group_id': message['group']['id']
                },
                message='博士，初次见面，这里是阿米娅2号，姐姐去了很远的地方，今后就由我来代替姐姐的工作吧，请多多指教哦'
            )

        if events_type == 'BotMuteEvent':
            self.leave_group(message['operator']['group']['id'])

        if events_type == 'BotLeaveEventKick':
            self.leave_group(message['group']['id'], False)

        if events_type == 'BotInvitedJoinGroupRequestEvent':
            self.handle_join_group(message, False)
