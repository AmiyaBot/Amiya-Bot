from database.sqlCombiner import Mysql, Formula, Where


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
                'function_use_num': Formula('function_use_num + 1')
            }
        )

    def set_disable_function(self, group_id, function_id, status=True):
        data = {
            'group_id': group_id,
            'function_id': function_id,
            'status': 1
        }
        if status:
            self.db.insert('t_function_disable', data=data)
        else:
            self.db.delete('t_function_disable', where=Where(data))

    def get_disable_function(self, group_id):
        result = self.db.select(
            't_function_disable',
            where=Where({
                'group_id': group_id,
            }),
            group='function_id'
        )

        return [item['function_id'] for item in result]

    def get_disable_function_groups(self, function_id):
        result = self.db.select(
            't_function_disable',
            where=Where({
                'function_id': function_id,
            }),
            group='function_id'
        )

        return [item['group_id'] for item in result]
