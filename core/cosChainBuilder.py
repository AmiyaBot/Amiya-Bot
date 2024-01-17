import os
import logging
import asyncio

from typing import Union
from amiyabot.adapters.tencent.qqGroup import QQGroupChainBuilder, QQGroupChainBuilderOptions
from build.uploadFile import COSUploader
from core.util import read_yaml, run_in_thread_pool


class COSQQGroupChainBuilder(QQGroupChainBuilder):
    def __init__(self, options: QQGroupChainBuilderOptions):
        super().__init__(options)

        self.config = read_yaml('config/cos.yaml')
        self.cos = COSUploader(
            self.config.secret_id,
            self.config.secret_key,
            logger_level=logging.NOTSET,
        )
        self.cos_caches = {}

    @property
    def domain(self):
        return self.config.domain + self.config.folder

    def start(self):
        ...

    def temp_filename(self, suffix: str):
        path, url = super().temp_filename(suffix)

        self.cos_caches[url] = f'{self.config.folder}/{os.path.basename(path)}'

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
        url = await super().get_image(image)

        self.cos.upload_file(
            self.file_caches[url],
            self.cos_caches[url],
        )

        return url

    async def get_voice(self, voice_file: str) -> str:
        url = await super().get_voice(voice_file)

        self.cos.upload_file(
            self.file_caches[url],
            self.cos_caches[url],
        )

        return url

    async def get_video(self, video_file: str) -> str:
        url = await super().get_video(video_file)

        self.cos.upload_file(
            self.file_caches[url],
            self.cos_caches[url],
        )

        return url
