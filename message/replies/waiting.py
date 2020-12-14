import json

from database.baseController import BaseController
from library.baiduCloud import OpticalCharacterRecognition

from functions.recruit.init import Init as Recruit

with open('config.json') as config:
    config = json.load(config)

ORC = OpticalCharacterRecognition(config['baidu_cloud'])
database = BaseController()
recruit = Recruit()


def waiting(data):
    user_id = data['user_id']
    user = database.user.get_user(user_id)

    if user and user[8]:
        wait = user[8]

        # 公招图像识别
        if wait == 'Recruit' and 'image' in data and data['image']:
            text = ''
            try:
                res = ORC.basic_general(data['image'])
                for item in res['words_result']:
                    text += item['words']
                database.user.set_waiting(user_id, '')
            except Exception as e:
                print('Recruit', e)
            finally:
                return recruit.action({
                    'text': text,
                    'user_id': user_id
                })
