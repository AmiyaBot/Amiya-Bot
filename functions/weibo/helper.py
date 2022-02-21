import re
import os
import time
import json
import aiohttp

from core.util import remove_xml_tag, char_seat, read_yaml, create_dir
from core.network.download import download_async
from core.database.group import GroupSetting
from core.database.messages import db
from core import log

weibo_conf = read_yaml('config/private/weibo.yaml')


async def get_result(url, headers):
    async with log.catch('requests error:'):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as res:
                if res.status == 200:
                    return json.loads(await res.text())


async def set_push_group():
    async with log.catch('group setting error:'):
        sql = 'select group_id, count(*) from message_record where msg_type = "group" group by group_id'
        counts = db.execute_sql(sql).fetchall()

        for item in counts:
            if int(item[1]) >= weibo_conf.autoPush.groupActivity:
                GroupSetting.insert(**{'send_weibo': 1, 'group_id': item[0]}).on_conflict(
                    conflict_target=[GroupSetting.group_id],
                    update={
                        GroupSetting.send_weibo: 1
                    }
                ).execute()


class WeiboContent:
    def __init__(self, html_text, detail_url, pics_list):
        self.html_text = html_text
        self.detail_url = detail_url
        self.pics_list = pics_list

    def __str__(self):
        return self.detail_url


class WeiboUser:
    def __init__(self, weibo_id: int):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Content-Type': 'application/json; charset=utf-8',
            'Referer': f'https://m.weibo.cn/u/{weibo_id}',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.url = f'https://m.weibo.cn/api/container/getIndex?uid={weibo_id}&type=uid&value={weibo_id}'

    async def get_cards_list(self):
        cards = []

        # 获取微博 container id
        result = await get_result(self.url, self.headers)
        if not result:
            return cards

        if 'tabsInfo' not in result['data']:
            return cards

        tabs = result['data']['tabsInfo']['tabs']
        container_id = ''
        for tab in tabs:
            if tab['tabKey'] == 'weibo':
                container_id = tab['containerid']

        # 获取正文列表
        result = await get_result(self.url + f'&containerid={container_id}', self.headers)
        if not result:
            return cards

        for item in result['data']['cards']:
            if item['card_type'] == 9 and 'isTop' not in item['mblog']:
                cards.append(item)

        return cards

    async def get_blog_list(self):
        cards = await self.get_cards_list()

        text = ''
        for index, item in enumerate(cards):
            detail = remove_xml_tag(item['mblog']['text']).replace('\n', ' ').strip()
            length = 0
            content = ''
            for char in detail:
                content += char
                length += char_seat(char)
                if length >= 32:
                    content += '...'
                    break

            date = item['mblog']['created_at']
            date = time.strptime(date, '%a %b %d %H:%M:%S +0800 %Y')
            date = time.strftime('%Y-%m-%d %H:%M:%S', date)

            text += f'\n[{index + 1}] {date}\n{content}\n'

        return text

    async def get_weibo_id(self, index: int):
        cards = await self.get_cards_list()
        if cards:
            return cards[index]['itemid']

    async def get_weibo_content(self, index: int):
        cards = await self.get_cards_list()

        if index >= len(cards):
            index = len(cards) - 1

        target_blog = cards[index]
        blog = target_blog['mblog']
        detail_url = target_blog['scheme']

        # 获取完整正文
        result = await get_result('https://m.weibo.cn/statuses/extend?id=' + blog['id'], self.headers)
        if not result:
            return None

        html_text = result['data']['longTextContent']
        html_text = re.sub('<br />', '\n', html_text)
        html_text = remove_xml_tag(html_text)
        html_text = html_text.strip('\n')

        # 获取静态图片列表
        pics_list = []
        pics = blog['pics'] if 'pics' in blog else []
        for pic in pics:
            pic_url = pic['large']['url']
            name = pic_url.split('/')[-1]
            suffix = name.split('.')[-1]

            if suffix.lower() == 'gif' and not weibo_conf.setting.sendGIF:
                continue

            path = f'{weibo_conf.setting.imagesCache}/{name}'
            create_dir(path, is_file=True)

            if not os.path.exists(path):
                stream = await download_async(pic_url, headers=self.headers)
                if stream:
                    open(path, 'wb').write(stream)

            pics_list.append(path)

        return WeiboContent(html_text, detail_url, pics_list)
