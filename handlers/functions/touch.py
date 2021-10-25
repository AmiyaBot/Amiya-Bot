import os
import random

from core import Chain, Message, AmiyaBot
from core.config import nudge
from dataSource.wiki import Wiki
from handlers.constraint import FuncInterface

wiki = Wiki()


@FuncInterface.is_disable_func(function_id='normal')
def random_reply(data: Message, bot: AmiyaBot):
    r = random.randint(1, 10)
    if r == 10:
        return get_voice(data)
    if r >= 7:
        bot.http.send_nudge(data.user_id, data.group_id)
        return False
    return get_face(data)


def get_face(data: Message):
    face_dir = 'resource/images/face/'
    images = []
    for root, dirs, files in os.walk(face_dir.strip('/')):
        for item in files:
            if item != '.gitkeep':
                images.append(face_dir + item)
    return Chain(data, quote=False).image(random.choice(images))


def get_voice(data: Message):
    # name = random.choice(['阿米娅', '阿米娅(近卫)'])
    name = '阿米娅'
    voice = random.choice(nudge)
    file = wiki.voice_exists(name, voice)
    if not file:
        file = wiki.download_operator_voices(name, voice)
        if not file:
            return Chain(data, quote=False).text('博士？[face32]')
    return Chain(data, quote=False).voice(file)
