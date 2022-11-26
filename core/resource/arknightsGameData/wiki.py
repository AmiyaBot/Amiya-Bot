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
    voices_cn_keys = {
        '任命助理': 'CN_001',
        '交谈1': 'CN_002',
        '交谈2': 'CN_003',
        '交谈3': 'CN_004',
        '晋升后交谈1': 'CN_005',
        '晋升后交谈2': 'CN_006',
        '信赖提升后交谈1': 'CN_007',
        '信赖提升后交谈2': 'CN_008',
        '信赖提升后交谈3': 'CN_009',
        '闲置': 'CN_010',
        '干员报到': 'CN_011',
        '观看作战记录': 'CN_012',
        '精英化晋升1': 'CN_013',
        '精英化晋升2': 'CN_014',
        '编入队伍': 'CN_017',
        '任命队长': 'CN_018',
        '行动出发': 'CN_019',
        '行动开始': 'CN_020',
        '选中干员1': 'CN_021',
        '选中干员2': 'CN_022',
        '部署1': 'CN_023',
        '部署2': 'CN_024',
        '作战中1': 'CN_025',
        '作战中2': 'CN_026',
        '作战中3': 'CN_027',
        '作战中4': 'CN_028',
        '完成高难行动': 'CN_029',
        '3星结束行动': 'CN_030',
        '非3星结束行动': 'CN_031',
        '行动失败': 'CN_032',
        '进驻设施': 'CN_033',
        '戳一下': 'CN_034',
        '信赖触摸': 'CN_036',
        '标题': 'CN_037',
        '问候': 'CN_042',
    }

    @classmethod
    def get_voice_path(cls,
                       source: str,
                       operator: Operator,
                       voice_key: str,
                       voice_type: str,
                       is_url: bool = False):
        tail = ''
        char_id = operator.id
        char_name = operator.wiki_name
        cn_key = cls.voices_cn_keys.get(voice_key)

        if voice_type == '_custom':
            tail = '_cn_topolect'

        if voice_type == '_ita':
            voice_type = '_custom'
            tail = '_ita'

        if is_url:
            return f'{source}/voice{voice_type}/{char_id}{tail}/{cn_key}.wav?filename={voice_key}.wav'

        return f'{source}/voice{voice_type}/{char_id}{tail}/{char_name}_{voice_key}.wav'

    @classmethod
    async def download_operator_voices(cls, filepath: str, operator: Operator, voice_key: str, voice_type: str = ''):
        async with log.catch('voices download error:'):
            url = cls.get_voice_path(remote_config.remote.wiki, operator, voice_key, voice_type, is_url=True)
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
