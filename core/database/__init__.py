import peewee

from typing import List, Any
from playhouse.migrate import *
from playhouse.shortcuts import model_to_dict
from core.util import read_yaml, create_dir, pascal_case_to_snake_case
from core import log

db_config = read_yaml('config/private/database.yaml')
is_mysql = False

if db_config.mysql.enabled:
    databases = db_config.mysql.databases
    is_mysql = True
else:
    databases = db_config.sqlite


class ModelClass(Model):
    @classmethod
    def batch_insert(cls, rows: List[dict], chunk_size: int = 200):
        if len(rows) > chunk_size:
            for batch in chunked(rows, chunk_size):
                cls.insert_many(batch).execute()
        else:
            cls.insert_many(rows).execute()

    @classmethod
    def insert_or_update(cls, insert: dict, update: dict = None, conflict_target: list = None, preserve: list = None):
        conflict = {
            'update': update,
            'preserve': preserve
        }
        if not is_mysql:
            conflict['conflict_target'] = conflict_target

        cls.insert(**insert).on_conflict(**conflict).execute()


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


def table(cls: ModelClass) -> Any:
    database: Database = cls._meta.database
    migrator: SchemaMigrator = SchemaMigrator.from_database(cls._meta.database)

    table_name = pascal_case_to_snake_case(cls.__name__)

    cls._meta.table_name = table_name
    cls.create_table()

    description = database.execute_sql(f'select * from `{table_name}` limit 1').description

    model_columns = [f for f, n in cls.__dict__.items() if type(n) in [peewee.FieldAccessor, peewee.ForeignKeyAccessor]]
    table_columns = [n[0] for n in description]

    migrate_list = []

    for f in set(model_columns) - set(table_columns):
        migrate_list.append(
            migrator.add_column(table_name, f, getattr(cls, f))
        )

    if migrate_list:
        migrate(*tuple(migrate_list))

    return cls


def connect_database(database):
    if is_mysql:
        return MySQLDatabase(database, **db_config.mysql.config)
    else:
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
                        fields: tuple = (),
                        join: dict = None,
                        order_by: tuple = None,
                        page: int = 1,
                        page_size: int = 10):
    model: ModelClass

    data = model.select(*fields)
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
