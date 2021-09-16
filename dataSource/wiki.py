import os
import traceback
import urllib.parse

from core.util import log
from core.util.common import make_folder
from core.util.config import nudge
from core.network.httpRequests import DownloadTools
from requests_html import HTMLSession, HTML

voices_source = 'resource/voices'


class Wiki(DownloadTools):
    def __init__(self):
        self.wiki_url = 'http://prts.wiki'
        self.wiki_session = HTMLSession()

    def get_page(self, url) -> HTML:
        req = self.wiki_session.get(url)
        return getattr(req, 'html')

    def get_voice_urls(self, name):
        html = self.get_page(f'http://prts.wiki/w/{name}/语音记录')
        files = {}
        for item in html.find('a[download]'):
            url = urllib.parse.unquote(item.attrs['href'])
            file_name = url.split('/')[-1]
            files[file_name] = url
        return files

    def request_pic_from_wiki(self, name):
        # noinspection PyBroadException
        try:
            html = self.get_page(f'{self.wiki_url}/w/文件:{name}.png')
            file = html.find('#file > a', first=True)
            furl = self.wiki_url + file.attrs['href']
            return self.request_file(furl, stringify=False)
        except Exception:
            log.error(traceback.format_exc(), stdout=False)
        return False

    def request_voice_from_wiki(self, operator, url, filename):
        file = f'{voices_source}/{operator}/{filename}'
        if os.path.exists(file):
            return file

        res = self.request_file(url, stringify=False)
        if res:
            make_folder(f'{voices_source}/{operator}')
            with open(file, mode='wb+') as src:
                src.write(res)
            return file

    def download_operator_voices(self, operator, name):
        try:
            urls = self.get_voice_urls(operator)
            filename = f'{operator}_{name}.wav'
            if filename in urls:
                return self.request_voice_from_wiki(operator, urls[filename], filename)
        except Exception as e:
            log.error(repr(e))
        return False

    def download_amiya_voices(self):
        try:
            voices = {
                'Amiya': '阿米娅',
                # 'AmiyaGuard': '阿米娅(近卫)'
            }
            for en, name in voices.items():
                urls = self.get_voice_urls(name)
                talks = [f'{name}_{item}.wav' for item in nudge]

                for file, status in log.download_src(urls, f'{en}Voices', _total=False):
                    if file in talks:
                        status.total += 1
                        res = self.request_voice_from_wiki(name, urls[file], file)
                        status.set_res(res)

        except Exception as e:
            log.error(repr(e))

    @staticmethod
    def voice_exists(operator, name):
        folder = f'{voices_source}/{operator}'
        file = f'{folder}/{operator}_{name}.wav'
        if not os.path.exists(file):
            make_folder(folder)
            return False
        return file
