from peewee import *
from typing import List
from playhouse.shortcuts import model_to_dict
from core.util import read_yaml, create_dir, pascal_case_to_snake_case

db_conf = read_yaml('config/private/database.yaml')
table_list: List[Model] = []


def table(cls: Model):
    cls._meta.table_name = pascal_case_to_snake_case(cls.__name__)
    cls.create_table()

    table_list.append(cls)

    return cls


def sqlite(database):
    create_dir(database, is_file=True)
    return SqliteDatabase(database, pragmas={
        'timeout': 30
    })


def query_to_list(query) -> List[dict]:
    return [model_to_dict(item) for item in query]
