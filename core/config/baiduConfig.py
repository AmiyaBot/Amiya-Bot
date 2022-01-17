class BaiduCloud:
    enable: bool
    appId: str
    apiKey: str
    secretKey: str

    @classmethod
    def desc(cls):
        return {
            'enable': False,
            'appId': None,
            'apiKey': None,
            'secretKey': None,
        }
