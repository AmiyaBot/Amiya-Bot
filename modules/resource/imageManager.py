import os
import sys
import json
import random

from requests_toolbelt.multipart.encoder import MultipartEncoder
from modules.network.httpRequests import HttpRequests
from database.baseController import BaseController

base = BaseController()


class Image:
    def __init__(self, source=None, imageId=None, url=None) -> None:
        self.source = source
        self.id = imageId
        self.url = url

    @staticmethod
    def from_id(id):
        return Image(imageId=id)

    def from_source(source):
        return Image(source=os.path.abspath(source))

    def to_chain(self):
        res = {
            "type": "Image",
            "path": None if self.source == None else self.source,
            "imageId": None if self.id == None else self.id,
            "url": None if self.url == None else self.url,
            "base64": None
        }
        return res


class ImageManager(HttpRequests):
    def __init__(self):
        super().__init__()

    def image(self, path: str, image_type='group'):

        if len(sys.argv) > 1 and sys.argv[1] == 'Test':
            return 'Test'

        resource = '/'.join(path.replace('\\', '/').split('/')[:-1])
        file_path = path
        image_id = self.find_image_id(file_path, image_type)
        if image_id:
            return Image.from_id(image_id)
        return Image.from_source(file_path)

    @staticmethod
    def find_image_id(file_path, image_type):
        results = base.resource.get_image_id(file_path, image_type)
        if results:
            return results['mirai_id']
        return False

    def requests_image_id(self, resource, file_path, image_type):
        multipart_data = MultipartEncoder(
            fields={
                'sessionKey': self.get_session(),
                'type': image_type,
                'img': (file_path.replace(resource, ''), open(file_path, 'rb'), 'application/octet-stream')
            },
            boundary=str(random.randint(int(1e28), int(1e29 - 1)))
        )
        headers = {'Content-Type': multipart_data.content_type}
        response = self.request.post(
            self.url('uploadImage'), data=multipart_data, headers=headers)
        if response.status_code == 200:
            data = json.loads(response.text)
            base.resource.add_image_id(file_path, image_type, data['imageId'])
            return data['imageId']
        return False
