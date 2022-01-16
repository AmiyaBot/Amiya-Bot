import re
import os
import datetime

from PIL import Image, ImageDraw, ImageFont
from typing import *
from core.util import create_dir
from core.config import config

FONTFILE = config.imageCreator.fontFile
SAVEPATH = config.imageCreator.savePath


class TextParser:
    def __init__(self, text: str, color: str, font_size: int, max_seat: int):
        self.font = ImageFont.truetype(FONTFILE, font_size)
        self.text = text
        self.color = color
        self.max_seat = max_seat
        self.char_list = []
        self.line = 0

        self.__parse()

    def __parse(self):
        text = self.text.strip('\n')
        search = re.findall(r'\[cl\s(.*?)@#(.*?)\scle]', text)

        color_pos = {0: self.color}

        for item in search:
            temp = f'[cl {item[0]}@#{item[1]} cle]'
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


class ImageElem:
    def __init__(self, path: str, size: int, pos: Tuple[int, int]):
        self.path = path
        self.pos = pos
        self.size = size


IMAGES_TYPE = List[Union[ImageElem, Dict[str, Any]]]


def create_image(text: str,
                 path: str = '',
                 width: int = 600,
                 height: int = None,
                 padding: int = 10,
                 font_size: int = 15,
                 line_height: int = 16,
                 color: str = '#000000',
                 bgcolor: str = '#ffffff',
                 images: IMAGES_TYPE = None):
    """
    文字转图片

        创建一张内容为 hello world 的图片：
        create_image('hello world')

        通过模板让 world 变为红色：
        create_image('hello [cl world@#ff0000 cle]')


    :param text:        主体文本
    :param path:        创建的文件夹路径
    :param width:       图片宽度
    :param height:      图片高度（默认为文本的最大占位）
    :param padding:     图片内边距
    :param font_size:   文字宽度
    :param line_height: 行高
    :param color:       文字默认颜色
    :param bgcolor:     图片背景色
    :param images:      插入的图片列表，内容为 ImageElem 对象
    :return:            图片路径
    """
    text = TextParser(text, color, font_size, width - padding * 2)
    image = Image.new('RGB', (width, height or ((text.line + 2) * line_height)), bgcolor)
    draw = ImageDraw.Draw(image)

    row = 0
    col = padding
    for line, item in enumerate(text.char_list):
        draw.text((col, padding + row * line_height), item[2], font=text.font, fill=item[1])
        col += item[3]
        if item[0]:
            row += 1
            col = padding

    if images:
        for item in images:
            if type(item) is dict:
                item = ImageElem(**item)
            if os.path.exists(item.path) is False:
                continue
            img = Image.open(item.path).convert('RGBA')

            pos = list(item.pos)
            width = int(height * (img.width / img.height))
            height = item.size
            offset = (height - width) / 2
            if offset:
                pos[0] += int(offset)

            img = img.resize(size=(width, height))
            image.paste(img, box=tuple(pos), mask=img)

    path = os.path.join(SAVEPATH, path)
    create_dir(path)

    path = os.path.join(path, '%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'))
    image.save(path)

    return path
