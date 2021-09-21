import re
import os
import datetime

from core.util.common import make_folder
from PIL import Image, ImageDraw, ImageFont

temp_dir = 'log/message'
font_file = 'resource/style/AdobeHeitiStd-Regular.otf'
logo_file = 'resource/style/rabbit.png'
logo_file_white = 'resource/style/rabbit-white.png'

line_height = 16
side_padding = 10


class TextParser:
    def __init__(self, text: str, color='#000000', font_size=15, max_seat=560):
        self.font = ImageFont.truetype(font_file, font_size)
        self.text = text
        self.color = color
        self.max_seat = max_seat
        self.char_list = []
        self.line = 0

        self.__parse()

    def __parse(self):
        text = self.text.strip('\n')
        search = re.findall(r'\[(.*?)@#(.*?)]', text)

        color_pos = {0: self.color}

        for item in search:
            temp = f'[{item[0]}@#{item[1]}]'
            index = text.index(temp)
            color_pos[index] = f'#{item[1]}'
            color_pos[index + len(item[0])] = self.color
            text = text.replace(temp, item[0], 1)

        length = 0
        sub_text = ''
        cur_color = self.color
        for idx, char in enumerate(text):
            if idx in color_pos:
                if cur_color != color_pos[idx] and sub_text:
                    self.__append_row(cur_color, sub_text, enter=False)
                    sub_text = ''
                cur_color = color_pos[idx]

            length += self.__font_seat(char)[0]
            sub_text += char

            is_end = idx == len(text) - 1
            if length >= self.max_seat or char == '\n' or is_end:
                enter = True
                if not is_end:
                    if text[idx + 1] == '\n' and sub_text != '\n' and sub_text[-1] != '\n':
                        enter = False

                self.__append_row(cur_color, sub_text, enter=enter)
                sub_text = ''
                length = 0

    def __append_row(self, color, text, enter=True):
        if enter:
            self.line += 1
        self.char_list.append(
            (enter, color, text, *self.__font_seat(text))
        )

    def __font_seat(self, char):
        return self.font.getsize_multiline(char)

    @staticmethod
    def char_seat(char):
        return 0.58 if 32 <= ord(char) <= 126 else 1

    @staticmethod
    def cut_code(code, length):
        code_list = re.findall('.{' + str(length) + '}', code)
        code_list.append(code[(len(code_list) * length):])
        res_list = []
        for n in code_list:
            if n != '':
                res_list.append(n)
        return res_list


def create_image(text: str, folder, images=None, font_size=15):
    text = TextParser(text, font_size=font_size)

    height = text.line + 2
    image = Image.new('RGB', (600, height * line_height), (245, 245, 245))
    draw = ImageDraw.Draw(image)
    font = text.font

    col = side_padding
    row = 0
    for line, item in enumerate(text.char_list):
        draw.text((col, side_padding + row * line_height), item[2], font=font, fill=item[1])
        col += item[3]
        if item[0]:
            row += 1
            col = side_padding

    icon = Image.open(logo_file)
    icon = icon.resize(size=(30, 30))
    image.alpha_composite(icon, box=(570, 0))

    if images:
        for item in images:
            if os.path.exists(item['path']) is False:
                continue
            img = Image.open(item['path']).convert('RGBA')
            img = img.resize(size=item['size'])
            image.alpha_composite(img, box=item['pos'])

    path = '%s/%s' % (temp_dir, folder)
    make_folder(path)

    name = '%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    path = '%s/%s' % (path, name)
    image.save(path)

    return path


def create_gacha_image(result: list):
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


def build_range(grids: list):
    _max = [0, 0, 0, 0]
    for item in [{'row': 0, 'col': 0}] + grids:
        row = item['row']
        col = item['col']
        if row <= _max[0]:
            _max[0] = row
        if row >= _max[1]:
            _max[1] = row
        if col <= _max[2]:
            _max[2] = col
        if col >= _max[3]:
            _max[3] = col

    width = abs(_max[2]) + _max[3] + 1
    height = abs(_max[0]) + _max[1] + 1

    empty = '　'
    block = '□'
    origin = '■'

    range_map = []
    for h in range(height):
        range_map.append([empty for w in range(width)])

    for item in grids:
        x = abs(_max[0]) + item['row']
        y = abs(_max[2]) + item['col']
        range_map[x][y] = block
    range_map[abs(_max[0])][abs(_max[2])] = origin

    return ''.join([''.join(item) + '\n' for item in range_map])
