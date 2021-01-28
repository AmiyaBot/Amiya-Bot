import pymysql
import threading


class Mysql:
    def __init__(self, config):
        self.db = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            db=config['db'],
            charset='utf8',
            autocommit=1
        )
        self.lock = threading.Lock()

    def __del__(self):
        self.close()

    def insert(self, table, data, update=None):
        keys = []
        values = []
        for key, value in data.items():
            value = str_or_int(value)
            keys.append(key)
            values.append(value)

        sql = 'insert into %s ( %s ) values ( %s )' % (table, ', '.join(keys), ', '.join(values))

        if update:
            values = []
            for key, value in update.items():
                if isinstance(value, Formula):
                    value = value.formula
                else:
                    value = str_or_int(value)
                values.append(' = '.join([key, value]))
            sql += ' on duplicate key update %s' % ', '.join(values)

        self.execute(sql)

    def batch_insert(self, table, data):
        keys = []
        values = []
        for index, item in enumerate(data):
            values_item = []
            for key, value in item.items():
                values_item.append(str_or_int(value))
                if index == 0:
                    keys.append(key)
            values.append('( %s )' % ', '.join(values_item))

        sql = 'insert into %s ( %s ) values %s' % (table, ', '.join(keys), ', '.join(values))

        self.execute(sql)

    def update(self, table, data: dict, where=None):
        values = []
        for key, value in data.items():
            if isinstance(value, Formula):
                value = value.formula
            else:
                value = str_or_int(value)
            values.append(' = '.join([key, value]))

        sql = 'update %s set %s' % (table, ', '.join(values))

        if where:
            sql += where.sql if isinstance(where, Where) else ' where %s' % where

        self.execute(sql)

    def delete(self, table, where):
        sql = 'delete from %s' % table
        sql += ' where %s' % ' and '.join(where)

        self.execute(sql)

    def select(self, table=None, fields=None, sql=None, where=None, fetchone=False):

        fields = [item[0] for item in self.execute('desc %s' % table).fetchall()] if table else fields

        if sql is None:
            sql = 'select * from %s' % table
            if where:
                sql += where.sql if isinstance(where, Where) else ' where %s' % where

        result = []
        for item in self.execute(sql).fetchall():
            result.append({field: item[index] for index, field in enumerate(fields)})

        if fetchone:
            return result[0] if len(result) else None
        return result

    def count(self, table, field, where=None):

        sql = 'select count( %s ) from %s' % (field, table)

        if where:
            sql += where.sql if isinstance(where, Where) else ' where %s' % where

        result = self.execute(sql).fetchone()
        return result[0]

    def truncate(self, table):
        self.execute('truncate %s' % table)

    def execute(self, sql):
        self.lock.acquire()
        cursor = None
        try:
            self.db.ping(reconnect=True)
            cursor = self.db.cursor()
            cursor.execute(sql)
        except Exception as e:
            print('Exec', e)
        finally:
            self.lock.release()
            return cursor

    def close(self):
        self.db.close()


class Formula:
    def __init__(self, formula: str):
        self.formula = formula


class Where:
    def __init__(self, data: dict, operator='AND'):
        values = []
        for key, value in data.items():
            if isinstance(value, Where):
                values.append('( %s )' % value.condition)
                continue
            if isinstance(value, list):
                values.append((' %s ' % value[0]).join(
                    [
                        key,
                        value[1].formula if isinstance(value[1], Formula) else str_or_int(value[1])
                    ]
                ))
                continue
            value = str_or_int(value)
            values.append(' = '.join([key, value]))

        self.condition = (' %s ' % operator).join(values)
        self.sql = ' where ' + self.condition


def str_or_int(value):
    return '"%s"' % value if isinstance(value, str) else str(value)
