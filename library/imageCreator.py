import re
import os
import time
import shutil
import datetime

from PIL import Image, ImageDraw, ImageFont

resource = 'resource/message'
font_file = 'resource/style/AdobeHeitiStd-Regular.otf'
logo_file = 'resource/style/rabbit.png'


def cut_code(code, length):
    code_list = re.findall('.{' + str(length) + '}', code)
    code_list.append(code[(len(code_list) * length):])
    return code_list


def create_image(text, message, images=None):
    text = text.split('\n')

    new_text = []
    for item in text:
        if len(item) > 34:
            for sub_item in cut_code(item, 34):
                if sub_item:
                    new_text.append(sub_item)
        else:
            new_text.append(item)

    text = '\n'.join(new_text)
    height = len(text.split('\n')) + 1
    image = Image.new('RGB', (510, height * 18), (255, 250, 250))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_file, 14)
    draw.text((10, 5), text, font=font, fill='#000000')

    icon = Image.open(logo_file)
    icon = icon.resize(size=(30, 30))
    image.paste(icon, box=(480, 0), mask=icon)

    if images:
        for item in images:
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


def clean_temp():
    for root, dirs, files in os.walk(resource):
        for item in dirs:
            if root == resource:
                shutil.rmtree(root + '/' + item)
