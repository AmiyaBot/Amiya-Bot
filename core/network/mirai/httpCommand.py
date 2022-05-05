from abc import abstractmethod, ABCMeta


class HttpCommand:
    class Api:
        def __init__(self, url: str, method: str = 'GET'):
            self.url = url
            self.method = method

    class MultiMedia(metaclass=ABCMeta):
        @classmethod
        @abstractmethod
        def UploadImage(cls, *args, **kwargs):
            raise NotImplementedError('UploadImage is not implemented.')

        @classmethod
        @abstractmethod
        def UploadVoice(cls, *args, **kwargs):
            raise NotImplementedError('UploadVoice is not implemented.')

        @classmethod
        @abstractmethod
        def UploadFile(cls, *args, **kwargs):
            raise NotImplementedError('UploadFile is not implemented.')
