class MapConfig:
    enable: bool
    key: str

    @classmethod
    def desc(cls):
        return {
            'enable': False,
            'key': ''
        }
