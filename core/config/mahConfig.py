class Port:
    http: int
    ws: int

    @classmethod
    def desc(cls):
        return {
            'http': 8080,
            'ws': 8060,
        }


class MiraiApiHttp:
    host: str
    port: Port
    authKey: str
    account: int

    @classmethod
    def desc(cls):
        return {
            'host': '127.0.0.1',
            'port': Port.desc(),
            'authKey': 'AmiyaBot',
            'account': None,
        }
