from peewee import *
from typing import List
from playhouse.shortcuts import model_to_dict
from core.util import create_dir, pascal_case_to_snake_case

collections: List[Model] = []


def table(cls: Model):
    cls._meta.table_name = pascal_case_to_snake_case(cls.__name__)
    cls.create_table()

    collections.append(cls)

    return cls


def sqlite(database):
    create_dir(database, is_file=True)
    return SqliteDatabase(database, pragmas={
        'timeout': 30
    })


def query_to_list(query) -> List[dict]:
    return [model_to_dict(item) for item in query]
