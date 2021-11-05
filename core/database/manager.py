from core import Message as MiraiMessage
from core.util import log
from playhouse.shortcuts import model_to_dict

from .models import *


class DataBase:
    @staticmethod
    def create_base():
        tables = (
            User,
            Admin,
            AdminTraceLog,
            Group,
            GroupActive,
            GroupSetting,
            DriftBottle,
            GroupNotice,
            Upload,
            Message,
            Function,
            Disable,
            Pool,
            PoolSpOperator,
            GachaConfig,
            Intellect,
            ReplaceText
        )
        for item in tables:
            item.create_table()


class SearchParams:
    def __init__(self, params: dict, equal: list = None, contains: list = None):
        self.equal = {}
        self.contains = {}

        if params:
            if equal:
                for item in equal:
                    if item in params:
                        self.equal[item] = params[item]

            if contains:
                for item in contains:
                    if item in params:
                        self.contains[item] = params[item]


def set_waiting(data: MiraiMessage, information=''):
    User.update(waiting=information).where(User.user_id == data.user_id).execute()


def exec_sql_file(file):
    with open(file, mode='r', encoding='utf-8') as f:
        sql = f.read().strip('\n').split('\n')
    for line in sql:
        if line.startswith('--'):
            continue
        try:
            sqlite_db.execute_sql(line)
        except Exception as e:
            log.error(f'sql exec error: {repr(e)}\n{line}')


def select_for_paginate(model,
                        search: SearchParams = None,
                        join: dict = None,
                        order_by: tuple = None,
                        page: int = 1,
                        page_size: int = 10):
    model: BaseModel

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
