import re
import os
import random

from message.messageType import Image
from modules.commonMethods import Reply, word_in_sentence
from database.baseController import BaseController

database = BaseController()
amiya_name = database.config.get_amiya_name()

face_dir = 'resource/images/face/'
images = []
for root, dirs, files in os.walk(face_dir.strip('/')):
    for item in files:
        if item != '.gitkeep':
            images.append(item)


def face_image(data):
    message = data['text'].strip()

    only_at = message == '' and data['is_at']

    if (only_at or eliminate_name(message)) and images:
        path = face_dir + random.choice(images)
        return Reply(Image(path), at=False)


def eliminate_name(message):
    if word_in_sentence(message, amiya_name[0]):
        for name in amiya_name[0]:
            message = message.replace(name, '')
        message = re.sub(r'\W', '', message).strip()
        if message == '':
            return True
    return False
