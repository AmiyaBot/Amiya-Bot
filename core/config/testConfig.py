class TestConfig:
    group: list
    enable: bool

    @classmethod
    def desc(cls):
        return {
            'group': [],
            'enable': False,
        }
