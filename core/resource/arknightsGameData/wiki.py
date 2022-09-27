from typing import Dict, List
from requests_html import HTMLSession, HTML
from amiyabot.network.download import download_async
from core.resource import remote_config
from core.util import create_dir
from core import log

from .operatorBuilder import Operator


class PRTS:
    real_name_dist: Dict[str, List[str]] = dict()
    voices_source = 'resource/voice'

    @classmethod
    def get_voice_path(cls,
                       source: str,
                       char_id: str,
                       char_name: str,
                       voice_key: str,
                       voice_type: str,
                       is_url: bool = False):
        t = '_cn_topolect' if is_url and voice_type == '_custom' else ''
        return f'{source}/voice{voice_type}/{char_id}{t}/{char_name}_{voice_key}.wav'

    @classmethod
    async def download_operator_voices(cls, filepath: str, operator: Operator, voice_key: str, voice_type: str = ''):
        async with log.catch('voices download error:'):
            url = cls.get_voice_path(remote_config.remote.wiki, operator.id, operator.wiki_name, voice_key, voice_type,
                                     is_url=True)

            res = await download_async(url)
            if res:
                create_dir(filepath, is_file=True)
                with open(filepath, mode='wb+') as src:
                    src.write(res)
                return filepath

    @classmethod
    async def get_real_name(cls, operator: str = None):
        if not cls.real_name_dist:
            async with log.catch('wiki error:'):
                url = 'https://prts.wiki/w/%E8%A7%92%E8%89%B2%E7%9C%9F%E5%90%8D'
                html: HTML = HTMLSession().get(url).html

                data = {}
                for table in html.find('.wikitable'):
                    trs = table.find('tr')[2:]
                    for tr in trs:
                        tds = tr.find('td')
                        name = tds[1].text
                        reel_name = tds[2].text.split('\n')

                        data[name] = reel_name

                cls.real_name_dist = data

        if operator:
            if operator in cls.real_name_dist:
                return cls.real_name_dist[operator]
            else:
                return []

        return cls.real_name_dist
