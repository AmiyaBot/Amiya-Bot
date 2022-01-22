class ServerConfig:
    host: str
    port: int

    @classmethod
    def desc(cls):
        return {
            'host': '127.0.0.1',
            'port': 5000,
        }
