import sys
import json
import random

from requests_toolbelt.multipart.encoder import MultipartEncoder
from modules.network.httpRequests import HttpRequests
from database.baseController import BaseController

base = BaseController()


class ImageManager(HttpRequests):
    def __init__(self, resource):
        super().__init__()

        self.resource = resource

    def image(self, file_name, image_type='group'):

        if len(sys.argv) > 1 and sys.argv[1] == 'Test':
            return 'Test'

        file_path = self.resource + file_name
        image_id = self.find_image_id(file_path, image_type)
        if image_id:
            return image_id
        return self.get_image_id(file_path, image_type)

    def find_image_id(self, file_name, image_type):
        results = base.resource.get_image_id(file_name, image_type)
        if results and len(results):
            return results[0][-1]
        return False

    def get_image_id(self, file_name, image_type):
        multipart_data = MultipartEncoder(
            fields={
                'sessionKey': self.get_session(),
                'type': image_type,
                'img': (file_name.replace(self.resource, ''), open(file_name, 'rb'), 'application/octet-stream')
            },
            boundary=str(random.randint(int(1e28), int(1e29 - 1)))
        )
        headers = {'Content-Type': multipart_data.content_type}
        response = self.request.post(self.url('uploadImage'), data=multipart_data, headers=headers)
        if response.status_code == 200:
            data = json.loads(response.text)
            base.resource.add_image_id(file_name, image_type, data['imageId'])
            return data['imageId']
        return False
