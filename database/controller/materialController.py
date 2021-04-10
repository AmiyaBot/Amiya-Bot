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

    def get_material_id(self, name=''):
        res = self.db.select('t_material', where=Where({
            'material_name': name
        }, operator='OR'), fetchone=True)

        return res['material_id']

    def find_material_source(self, name):
        return self.db.select('t_material_source', where=Where({
            'material_id': self.get_material_id(name=name)
        }))

    def find_material_made(self, name):
        sql = 'SELECT m.material_name, t.use_number FROM t_material_made t ' \
              'LEFT JOIN t_material m ON t.use_material_id = m.material_id ' \
              'WHERE t.material_id = %s' % self.get_material_id(name=name)

        return self.db.select(sql=sql, fields=['material_name', 'use_number'])

    def update_stage(self, data):
        self.db.truncate('t_stage')
        self.db.batch_insert('t_stage', data=data)

    def truncate_all(self):
        tables = [
            't_material',
            't_material_made',
            't_material_source',
            't_operator',
            't_operator_evolve_costs',
            't_operator_skill',
            't_operator_skill_description',
            't_operator_skill_mastery_costs',
            't_operator_stories',
            't_operator_tags_relation',
            't_operator_voice'
        ]
        for item in tables:
            self.db.truncate(item)
