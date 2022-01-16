from graiax import silkcoder
from core.network.httpSessionClient import HttpSessionClient


class ResourceManager:
    http = HttpSessionClient()

    @classmethod
    async def get_image_id(cls, path, msg_type):
        return await cls.http.upload_image(open(path, mode='rb'), msg_type)

    @classmethod
    async def get_voice_id(cls, path, msg_type):
        return await cls.http.upload_voice(await silkcoder.encode(path), msg_type)
