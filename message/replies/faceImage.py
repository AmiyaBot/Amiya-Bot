import re
import os
import json
import random

from message.messageType import MessageType
from modules.resource.imageManager import ImageManager
from modules.commonMethods import Reply, word_in_sentence

MSG = MessageType()
IM = ImageManager('resource/images/face/')

images = []
for root, dirs, files in os.walk('resource/images/face'):
    for item in files:
        if item != '.gitkeep':
            images.append(item)

with open('resource/words/amiyaName.json', encoding='utf-8') as file:
    amiya_name = json.load(file)


def faceImage(data):
    message = data['text'].strip()

    only_at = message == '' and data['is_at']

    if only_at or eliminate_name(message):
        image_id = IM.image(random.choice(images), data['type'])
        if image_id:
            return Reply([MSG.image(image_id)], at=False)


def eliminate_name(message):
    if word_in_sentence(message, amiya_name[0]):
        for name in amiya_name[0]:
            message = message.replace(name, '')
        message = re.sub(r'\W', '', message).strip()
        if message == '':
            return True
    return False
