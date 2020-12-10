import random
import json
import os

from requests_toolbelt.multipart.encoder import MultipartEncoder
from modules.network.httpRequests import HttpRequests
from database.baseController import BaseController

base = BaseController()


class VoiceManager(HttpRequests):
    def __init__(self, resource=''):
        super().__init__()

        self.resource = resource

    def save_voice_files(self):
        for root, dirs, files in os.walk(self.resource):
            for item in files:
                if self.find_voice_id(item) is False:
                    self.get_voice_id(item)

    def find_voice_id(self, file_name, voice_type='group'):

        if '.wav' not in file_name:
            file_name = '%s.wav' % file_name

        results = base.resource.get_voice_id(file_name, voice_type)
        if results and len(results):
            return results[0][-1]
        return False

    def get_voice_id(self, file_name, voice_type='group'):
        multipart_data = MultipartEncoder(
            fields={
                'sessionKey': self.get_session(),
                'type': voice_type,
                'voice': (file_name, open(self.resource + '/' + file_name, 'rb'), 'application/octet-stream')
            },
            boundary=str(random.randint(int(1e28), int(1e29 - 1)))
        )
        headers = {'Content-Type': multipart_data.content_type}
        response = self.request.post(self.url('uploadVoice'), data=multipart_data, headers=headers)

        print(file_name, response.status_code, response.text)

        if response.status_code == 200:
            data = json.loads(response.text)
            base.resource.add_voice_id(file_name, voice_type, data['voiceId'])
