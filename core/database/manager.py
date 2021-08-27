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


def exec_sql_file(file):
    with open(file, mode='r', encoding='utf-8') as f:
        sql = f.read().strip('\n').split('\n')
    for line in sql:
        try:
            sqlite_db.execute_sql(line)
        except Exception as e:
            log.error(f'sql exec error: {repr(e)}\n{line}')
