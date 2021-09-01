import random

from requests_toolbelt.multipart.encoder import MultipartEncoder
from core.network.httpRequests import MiraiHttp
from core.database.models import Images


class ImageManager(MiraiHttp):
    def __init__(self):
        super().__init__()

    def image(self, path: str, image_type: str):
        rec: Images = Images.get_or_none(image_path=path, image_type=image_type)
        if rec:
            return rec.mirai_id

        resource = '/'.join(path.replace('\\', '/').split('/')[:-1])
        file_path = path
        multipart_data = MultipartEncoder(
            fields={
                'sessionKey': self.get_session(),
                'type': image_type,
                'img': (file_path.replace(resource, ''), open(file_path, 'rb'), 'application/octet-stream')
            },
            boundary=str(random.randint(int(1e28), int(1e29 - 1)))
        )
        mirai_id = self.get_image_id(multipart_data)

        Images.create(image_path=path, image_type=image_type, mirai_id=mirai_id)

        return mirai_id
