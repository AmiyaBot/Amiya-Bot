import os
import re
import time
import requests
import traceback

from core import Message, Chain
from core.util import log
from core.config import func_setting
from core.util.common import remove_xml_tag, make_folder
from core.util.imageCreator import TextParser
from handlers.constraint import FuncInterface

weibo_id = '6279793937'


class Weibo(FuncInterface):
    def __init__(self):
        super().__init__(function_id='weibo')

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Content-Type': 'application/json; charset=utf-8',
            'Referer': f'https://m.weibo.cn/u/{weibo_id}',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.url = f'https://m.weibo.cn/api/container/getIndex?uid={weibo_id}&type=uid&value={weibo_id}'

    @FuncInterface.is_disable
    def verify(self, data: Message):
        for item in ['新公告', '新动态', '新消息', '微博']:
            if item in data.text:
                return True

    @FuncInterface.is_used
    def action(self, data: Message):
        message = data.text_digits

        reply = Chain(data)
        index = 0

        r = re.search(re.compile(r'第(\d+)条微博'), message)
        if r:
            index = abs(int(r.group(1)))

        if '最新' in message:
            index = 1

        if index:
            # noinspection PyBroadException
            try:
                result, detail_url, pics_list = self.requests_content(index - 1)
                reply.text(detail_url + '\n')
                reply.text(result)
                if pics_list:
                    for pic in pics_list:
                        reply.image(pic)
                return reply
            except Exception:
                log.error(traceback.format_exc())
                return reply.text('博士…暂时无法获取微博呢…请稍后再试吧')
        else:
            result = self.get_blog_list()
            return reply.text(result)

    def requests_content(self, index: int, only_id=False):
        session = requests.session()

        cards = self.get_cards_list()

        target_blog = cards[index]
        blog = target_blog['mblog']
        detail_url = target_blog['scheme']
        item_id = target_blog['itemid']

        if only_id:
            return item_id

        # 获取完整正文
        url = 'https://m.weibo.cn/statuses/extend?id=' + blog['id']
        result = session.get(url, headers=self.headers).json()
        html_text = result['data']['longTextContent']
        html_text = re.sub('<br />', '\n', html_text)
        html_text = remove_xml_tag(html_text)
        html_text = html_text.strip('\n')

        # 获取静态图片列表
        setting = func_setting().weiboSetting
        pics_list = []
        pics = blog['pics'] if 'pics' in blog else []
        for pic in pics:
            pic_url = pic['large']['url']
            name = pic_url.split('/')[-1]
            suffix = name.split('.')[-1]
            if suffix.lower() == 'gif' and not setting.weiboSendGIF:
                continue
            temp = 'log/weibo'
            path = f'{temp}/{name}'
            make_folder(temp)
            if os.path.exists(path) is False:
                stream = requests.get(pic_url, headers=self.headers, stream=True)
                if stream.status_code == 200:
                    open(path, 'wb').write(stream.content)

            pics_list.append(path)

        return html_text, detail_url, pics_list

    def get_cards_list(self):
        session = requests.session()
        cards = []

        try:
            # 获取微博 container id
            result = session.get(self.url, headers=self.headers).json()

            if 'tabsInfo' not in result['data']:
                return []

            tabs = result['data']['tabsInfo']['tabs']
            container_id = ''
            for tab in tabs:
                if tab['tabKey'] == 'weibo':
                    container_id = tab['containerid']

            # 获取正文列表
            result = session.get(self.url + f'&containerid={container_id}', headers=self.headers).json()

            for item in result['data']['cards']:
                if item['card_type'] == 9 and 'isTop' not in item['mblog']:
                    cards.append(item)

        except requests.exceptions.SSLError:
            pass

        return cards

    def get_blog_list(self):

        cards = self.get_cards_list()

        text = '博士，这是【明日方舟Arknights】最近的微博列表。\n'

        for index, item in enumerate(cards):
            detail = remove_xml_tag(item['mblog']['text']).replace('\n', ' ').replace('#明日方舟#', '').strip()
            length = 0
            content = ''
            for char in detail:
                content += char
                length += TextParser.char_seat(char)
                if length >= 32:
                    content += '...'
                    break

            date = item['mblog']['created_at']
            date = time.strptime(date, '%a %b %d %H:%M:%S +0800 %Y')
            date = time.strftime('%Y-%m-%d %H:%M:%S', date)

            text += f'\n【{index + 1}】{date}\n{content}\n'

        text += '\n请和我说「阿米娅查看第 N 条微博」来获取详情吧'

        return text
