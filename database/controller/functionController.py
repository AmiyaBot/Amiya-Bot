from database.sqlCombiner import Mysql, Calc, Where


class Function:
    def __init__(self, db: Mysql):
        self.db = db

    def add_function_use_num(self, function_id):
        self.db.insert(
            table='t_function',
            data={
                'function_id': function_id,
                'function_use_num': 1
            },
            update={
                'function_use_num': Calc('function_use_num + 1')
            }
        )
