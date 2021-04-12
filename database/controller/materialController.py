from database.sqlCombiner import Mysql, Formula, Where


class Material:
    def __init__(self, db: Mysql):
        self.db = db

    def add_material(self, data):
        self.db.batch_insert('t_material', data=data)

    def add_material_source(self, data):
        self.db.batch_insert('t_material_source', data=data)

    def add_material_made(self, data):
        self.db.batch_insert('t_material_made', data=data)

    def get_all_material(self):
        return self.db.select('t_material')

    def get_material(self, name=''):
        return self.db.select('t_material', where=Where({
            'material_name': name
        }, operator='OR'), fetchone=True)

    def find_material_source(self, name, only_main=False):
        field = ', '.join([
            'st.stage_code',
            'st.stage_name',
            'ms.source_rate'
        ])
        left_join = ' '.join([
            'LEFT JOIN t_stage st ON st.stage_id = ms.source_place',
            'LEFT JOIN t_material m ON m.material_id = ms.material_id'
        ])

        sql = 'SELECT stage_id FROM t_stage'
        sql = 'SELECT %s FROM t_material_source ms %s ' \
              'WHERE m.material_name = "%s" AND ms.source_place IN (%s)' % (field, left_join, name, sql)

        if only_main:
            sql += ' AND (st.stage_id LIKE "main%" OR st.stage_id LIKE "sub%" OR st.stage_id LIKE "wk%")'

        return self.db.select(sql=sql, fields=[
            'stage_code',
            'stage_name',
            'source_rate'
        ])

    def find_material_made(self, name):
        field = ', '.join([
            'ml.material_name',
            'ml.material_icon',
            'mm.use_number',
            'mm.made_type'
        ])
        left_join = ' '.join([
            'LEFT JOIN t_material m ON m.material_id = mm.material_id',
            'LEFT JOIN t_material ml ON ml.material_id = mm.use_material_id'
        ])

        sql = 'SELECT %s FROM t_material_made mm %s WHERE m.material_name = "%s"' % (field, left_join, name)

        return self.db.select(sql=sql, fields=[
            'material_name',
            'material_icon',
            'use_number',
            'made_type'
        ])

    def update_stage(self, data):
        self.db.truncate('t_stage')
        self.db.batch_insert('t_stage', data=data)

    def delete_all_data(self):
        tables = [
            't_material',
            't_material_made',
            't_material_source'
        ]
        for item in tables:
            self.db.truncate(item)
