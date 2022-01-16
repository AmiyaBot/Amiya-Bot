class SpeedSetting:
    maxsize: int
    mintime: int

    @classmethod
    def desc(cls):
        return {
            'maxsize': 3,
            'mintime': 10,
        }
