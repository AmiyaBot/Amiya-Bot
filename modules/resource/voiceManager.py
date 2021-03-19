import sys
import json
import random

from requests_toolbelt.multipart.encoder import MultipartEncoder
from modules.network.httpRequests import HttpRequests
from database.baseController import BaseController

base = BaseController()


class VoiceManager(HttpRequests):
    def __init__(self):
        super().__init__()

    def voice(self, path: str, voice_type='group'):

        if len(sys.argv) > 1 and sys.argv[1] == 'Test':
            return 'Test'

        resource = '/'.join(path.replace('\\', '/').split('/')[:-1])
        file_path = path
        voice_id = self.find_voice_id(file_path, voice_type)
        if voice_id:
            return voice_id
        return self.requests_voice_id(resource, file_path, voice_type)

    @staticmethod
    def find_voice_id(file_path, voice_type):
        results = base.resource.get_voice_id(file_path, voice_type)
        if results:
            return results['mirai_id']
        return False

    def requests_voice_id(self, resource, file_path, voice_type):
        multipart_data = MultipartEncoder(
            fields={
                'sessionKey': self.get_session(),
                'type': voice_type,
                'voice': (file_path.replace(resource, ''), open(file_path, 'rb'), 'application/octet-stream')
            },
            boundary=str(random.randint(int(1e28), int(1e29 - 1)))
        )
        headers = {'Content-Type': multipart_data.content_type}
        response = self.request.post(self.url('uploadVoice'), data=multipart_data, headers=headers)
        if response.status_code == 200:
            data = json.loads(response.text)
            base.resource.add_voice_id(file_path, voice_type, data['voiceId'])
            return data['voiceId']
        return False
