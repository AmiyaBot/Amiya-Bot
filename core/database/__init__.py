from peewee import *
from typing import List
from playhouse.shortcuts import model_to_dict
from core.util import read_yaml, create_dir, pascal_case_to_snake_case
from core import log

db_conf = read_yaml('config/private/database.yaml')
table_list: List[Model] = []


class Model(Model):
    @classmethod
    def insert_data(cls, rows):
        for batch in chunked(rows, 100):
            cls.insert_many(batch).execute()


class SearchParams:
    def __init__(self, params, equal: list = None, contains: list = None):
        self.equal = {}
        self.contains = {}

        if equal:
            for item in equal:
                value = getattr(params, item)
                if value:
                    self.equal[item] = value

        if contains:
            for item in contains:
                value = getattr(params, item)
                if value:
                    self.contains[item] = value


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


def exec_sql_file(file, db):
    with open(file, mode='r', encoding='utf-8') as f:
        sql = f.read().strip('\n').split('\n')
    for line in sql:
        if line.startswith('--'):
            continue
        try:
            db.execute_sql(line)
        except Exception as e:
            log.error(e, desc='Execute error:')


def select_for_paginate(model,
                        search: SearchParams = None,
                        join: dict = None,
                        order_by: tuple = None,
                        page: int = 1,
                        page_size: int = 10):
    model: Model

    data = model.select()
    where = []

    if search:
        if search.equal:
            for name, value in search.equal.items():
                if hasattr(model, name) and value != '':
                    where.append(
                        getattr(model, name) == value
                    )
        if search.contains:
            for name, value in search.contains.items():
                if hasattr(model, name) and value != '':
                    where.append(
                        getattr(model, name).contains(value)
                    )

    if where:
        data = data.where(*tuple(where))

    if join:
        data = data.join(**join)

    if order_by:
        data = data.order_by(*order_by)

    count = data.count()
    query = data.paginate(page=page, paginate_by=page_size)

    results = [model_to_dict(item) for item in query]

    return results, count
