import sys
import logging

from typing import Union
from qcloud_cos import CosConfig, CosS3Client, CosClientError, CosServiceError

# 官方发布桶（cos.amiyabot.com 的源站）；运行时图床等非发布场景请显式传 bucket
official_bucket = 'amiyabot-1302462817'


class COSUploader:
    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        region: str = 'ap-guangzhou',
        bucket: str = None,
        logger_level: int = logging.DEBUG,
    ):
        if logger_level:
            logging.basicConfig(level=logger_level, stream=sys.stdout)

        self.bucket = bucket or self.get_bucket_by_index(0)
        self.client = CosS3Client(CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key))

        print(f'COSUploader: bucket={self.bucket} region={region}')

    def get_bucket_by_index(self, index: int):
        buckets = self.client.list_buckets().get('Buckets', {}).get('Bucket', [])

        # 账号只有一个桶时，SDK 返回 dict 而非 list
        if isinstance(buckets, dict):
            buckets = [buckets]

        return buckets[index]['Name']

    def upload_file(self, file: str, target: str, resume_times: int = 10):
        for i in range(0, resume_times):
            try:
                self.client.upload_file(
                    Bucket=self.bucket,
                    LocalFilePath=file,
                    Key=target,
                )
                break
            except (CosClientError, CosServiceError) as e:
                print(f'upload retry {i + 1}/{resume_times}: {file} -> {target}\n{e}')
        else:
            raise CosClientError(f'upload failed after {resume_times} retries: {file} -> {target}')

    def delete_file(self, files: Union[list, str]):
        if type(files) is not list:
            files = [files]

        delete_list = []
        for file in files:
            delete_list.append({'Key': file})

        return self.client.delete_objects(
            Bucket=self.bucket,
            Delete={
                'Quiet': 'true',
                'Object': delete_list,
            },
        )

    def delete_folder(self, folders: Union[list, str], max_keys: int = 100):
        if type(folders) is not list:
            folders = [folders]

        file_list = []

        for folder in folders:
            marker = ''
            complete = False
            while not complete:
                response = self.client.list_objects(Bucket=self.bucket, Prefix=folder, Marker=marker, MaxKeys=max_keys)

                if 'Contents' in response:
                    file_list += [item['Key'] for item in response['Contents']]

                if 'NextMarker' in response:
                    marker = response['NextMarker']

                if response['IsTruncated'] == 'false':
                    complete = True

        if file_list:
            self.delete_file(file_list)
