from .models import *


class DataBase:
    @staticmethod
    def create_base():
        tables = (
            User,
            Group,
            Images,
            Message,
            Function,
            Disable,
            Pool,
            Intellect
        )
        for item in tables:
            item.create_table()
