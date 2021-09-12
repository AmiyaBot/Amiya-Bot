import re
import os
import datetime

from core.util.common import make_folder
from PIL import Image, ImageDraw, ImageFont

temp_dir = 'log/message'
font_file = 'resource/style/AdobeHeitiStd-Regular.otf'
logo_file = 'resource/style/rabbit.png'
logo_file_white = 'resource/style/rabbit-white.png'


def cut_code(code, length):
    code_list = re.findall('.{' + str(length) + '}', code)
    code_list.append(code[(len(code_list) * length):])
    res_list = []
    for n in code_list:
        if n != '':
            res_list.append(n)
    return res_list


def char_seat(char):
    return 0.5 if 32 <= ord(char) <= 126 else 1


def split_text(text, max_seat=36):
    text = text.strip('\n').split('\n')

    new_text = []
    for item in text:

        item_len = 0
        item_sub = ''

        for char in item:
            item_len += char_seat(char)
            item_sub += char
            if item_len >= max_seat:
                item_len = 0
                item_sub += '\n'

        new_text.append(item_sub)

    return '\n'.join(new_text).split('\n')


def create_image(text: str, folder, images=None):
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

    path = '%s/%s' % (temp_dir, folder)
    make_folder(path)

    name = '%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    path = '%s/%s' % (path, name)
    image.save(path)

    return path


def create_gacha_result(result: list):
    image = Image.open('resource/images/gacha/bg.png')
    draw = ImageDraw.ImageDraw(image)

    x = 78
    for item in result:
        if item is None:
            x += 82
            continue

        rarity = 'resource/images/gacha/%s.png' % item['rarity']
        if os.path.exists(rarity):
            img = Image.open(rarity).convert('RGBA')
            image.paste(img, box=(x, 0), mask=img)

        if 'temp_photo' in item and item['temp_photo']:
            photo = item['temp_photo']
        else:
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

    icon = Image.open(logo_file_white)
    icon = icon.resize(size=(30, 30))
    image.paste(icon, box=(image.size[0] - 30, 0), mask=icon)

    path = '%s/Gacha' % temp_dir
    make_folder(path)

    name = '%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    path = '%s/%s' % (path, name)

    x, y = image.size
    image = image.resize((int(x * 0.8), int(y * 0.8)), Image.ANTIALIAS)
    image.save(path, quality=80)

    return path
