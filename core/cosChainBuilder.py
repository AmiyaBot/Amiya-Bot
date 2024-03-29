import os
import logging
import asyncio

from typing import Union, Optional
from amiyabot.adapters.tencent.qqGroup import QQGroupChainBuilder, QQGroupChainBuilderOptions
from build.uploadFile import COSUploader
from core.util import run_in_thread_pool
from core.config import cos_config


class COSQQGroupChainBuilder(QQGroupChainBuilder):
    def __init__(self, options: QQGroupChainBuilderOptions):
        super().__init__(options)

        self.cos: Optional[COSUploader] = None
        self.cos_caches = {}

        if cos_config.secret_id and cos_config.secret_key:
            self.cos = COSUploader(
                cos_config.secret_id,
                cos_config.secret_key,
                logger_level=logging.NOTSET,
            )

    @property
    def domain(self):
        return cos_config.domain + cos_config.folder

    def start(self):
        ...

    def temp_filename(self, suffix: str):
        path, url = super().temp_filename(suffix)

        self.cos_caches[url] = f'{cos_config.folder}/{os.path.basename(path)}'

        return path, url

    def remove_file(self, url: str):
        super().remove_file(url)

        if url in self.cos_caches:
            asyncio.create_task(
                run_in_thread_pool(
                    self.cos.client.delete_object,
                    self.cos.bucket,
                    self.cos_caches[url],
                )
            )
            del self.cos_caches[url]

    async def get_image(self, image: Union[str, bytes]) -> Union[str, bytes]:
        if isinstance(image, str) and image.startswith('http'):
            return image

        url = await super().get_image(image)

        self.cos.upload_file(
            self.file_caches[url],
            self.cos_caches[url],
        )

        return url

    async def get_voice(self, voice_file: str) -> str:
        if voice_file.startswith('http'):
            return voice_file

        url = await super().get_voice(voice_file)

        self.cos.upload_file(
            self.file_caches[url],
            self.cos_caches[url],
        )

        return url

    async def get_video(self, video_file: str) -> str:
        if video_file.startswith('http'):
            return video_file

        url = await super().get_video(video_file)

        self.cos.upload_file(
            self.file_caches[url],
            self.cos_caches[url],
        )

        return url
