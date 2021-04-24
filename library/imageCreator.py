import re
import os
import shutil
import datetime

from PIL import Image, ImageDraw, ImageFont
from modules.config import get_config

resource = 'resource/message'
font_file = 'resource/style/AdobeHeitiStd-Regular.otf'
logo_file = 'resource/style/rabbit.png'

# 配置 mirai-api-http 的缓存路径可以顺手清理其缓存的图片
console_temp = get_config('message.console_temp_images')


def cut_code(code, length):
    code_list = re.findall('.{' + str(length) + '}', code)
    code_list.append(code[(len(code_list) * length):])
    res_list = []
    for n in code_list:
        if n != '':
            res_list.append(n)
    return res_list


def split_text(text):
    text = text.strip('\n').split('\n')

    new_text = []
    for item in text:
        if len(item) > 38:
            for sub_item in cut_code(item, 38):
                if sub_item:
                    new_text.append(sub_item)
        else:
            new_text.append(item)

    return new_text


def create_image(text: str, message, images=None):
    text = '\n'.join(split_text(text))
    height = len(text.split('\n')) + 1
    image = Image.new('RGB', (550, height * 18), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_file, 14)
    draw.text((10, 5), text, font=font, fill='#000000')

    icon = Image.open(logo_file)
    icon = icon.resize(size=(30, 30))
    image.paste(icon, box=(520, 0), mask=icon)

    if images:
        for item in images:
            if os.path.exists(item['path']) is False:
                continue
            img = Image.open(item['path']).convert('RGBA')
            img = img.resize(size=item['size'])
            image.paste(img, box=item['pos'], mask=img)

    path = '%s/%s' % (resource, message)
    if os.path.exists(path) is False:
        os.mkdir(path)

    name = '%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    path = '%s/%s' % (path, name)
    image.save(path)

    return name


def create_gacha_result(result: list):
    image = Image.open('resource/images/gacha/bg.png')
    draw = ImageDraw.ImageDraw(image)

    x = 78
    for item in result:

        rarity = 'resource/images/gacha/%s.png' % item['rarity']
        if os.path.exists(rarity):
            img = Image.open(rarity).convert('RGBA')
            image.paste(img, box=(x, 0), mask=img)

        photo = 'resource/images/photo/%s_1.png' % item['photo']
        if os.path.exists(photo):
            img = Image.open(photo).convert('RGBA')

            radio = 252 / img.size[1]

            width = int(img.size[0] * radio)
            height = int(img.size[1] * radio)

            step = int((width - 82) / 2)
            crop = (step, 0, width - step, height)

            img = img.resize(size=(width, height))
            img = img.crop(crop)
            image.paste(img, box=(x, 112), mask=img)

        draw.rectangle((x + 10, 321, x + 70, 381), fill='white')
        class_img = 'resource/images/class/%s.png' % item['class']
        if os.path.exists(class_img):
            img = Image.open(class_img).convert('RGBA')
            img = img.resize(size=(59, 59))
            image.paste(img, box=(x + 11, 322), mask=img)

        x += 82

    path = '%s/Gacha' % resource
    if os.path.exists(path) is False:
        os.mkdir(path)
    name = '%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    path = '%s/%s' % (path, name)

    x, y = image.size
    image = image.resize((int(x * 0.8), int(y * 0.8)), Image.ANTIALIAS)
    image.save(path, quality=80)

    return name


def clean_temp_images():
    for root, dirs, files in os.walk(resource):
        for item in dirs:
            if root == resource:
                shutil.rmtree(root + '/' + item)

    if os.path.exists(console_temp):
        shutil.rmtree(console_temp)
        os.mkdir(console_temp)
