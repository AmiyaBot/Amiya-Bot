import sys
import logging

from typing import Union
from qcloud_cos import CosConfig, CosS3Client, CosClientError, CosServiceError


class COSUploader:
    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        region: str = 'ap-guangzhou',
        bucket: str = None,
        logger_level: int = logging.DEBUG,
    ):
        logging.basicConfig(level=logger_level, stream=sys.stdout)
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)

        self.client = CosS3Client(config)
        self.bucket = bucket or self.get_bucket_by_index(0)

    def get_bucket_by_index(self, index: int):
        return self.client.list_buckets()['Buckets']['Bucket'][index]['Name']

    def upload_file(self, file: str, target: str, resume_times: int = 10):
        for i in range(0, resume_times):
            try:
                self.client.upload_file(
                    Bucket=self.bucket,
                    LocalFilePath=file,
                    Key=target,
                )
                break
            except CosClientError or CosServiceError as e:
                print(e)

    def delete_file(self, files: Union[list, str]):
        if type(files) is not list:
            files = [files]

        delete_list = []
        for file in files:
            delete_list.append({'Key': file})

        self.client.delete_objects(Bucket=self.bucket, Delete={'Object': delete_list})

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
