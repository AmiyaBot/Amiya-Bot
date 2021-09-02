from core.network.httpRequests import MiraiHttp
from core.database.models import Upload


class ImageManager(MiraiHttp):
    def __init__(self):
        super().__init__()

    def image(self, path: str, image_type: str):
        rec: Upload = Upload.get_or_none(path=path, type=image_type)
        if rec:
            return rec.mirai_id

        mirai_id = self.get_mirai_id(path, image_type, _t='image')

        Upload.create(path=path, type=image_type, mirai_id=mirai_id)

        return mirai_id
