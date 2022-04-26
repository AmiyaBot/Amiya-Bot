from graiax import silkcoder
from core.network.mirai.httpClient import HttpClient


class ResourceManager:
    http = HttpClient()

    @classmethod
    async def get_image_id(cls, target, msg_type):
        if type(target) is str:
            with open(target, mode='rb') as file:
                target = file.read()

        return await cls.http.upload_image(target, msg_type)

    @classmethod
    async def get_voice_id(cls, path, msg_type):
        return await cls.http.upload_voice(await silkcoder.async_encode(path), msg_type)
