class CovidData:
    reloadTime: int
    reloadRequestTimes: int

    @classmethod
    def desc(cls):
        return {
            'reloadTime': 600,
            'reloadRequestTimes': 1000
        }
