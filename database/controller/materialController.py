class Material:
    def __init__(self, db):
        self.db = db

    def get_all_material(self):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_material'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def add_material(self, materials):
        cursor = self.db.cursor()

        values = []
        for item in materials:
            value = [
                '"%s"' % item['id'],
                '"%s"' % item['name'],
                '"%s"' % item['nickname']
            ]
            value = ', '.join(value)
            values.append('(%s)' % value)

        sql = 'INSERT INTO t_material ( material_id, material_name, material_nickname ) ' \
              'VALUES %s' % ', '.join(values)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def add_material_source(self, materials):
        cursor = self.db.cursor()

        values = []
        for item in materials:
            value = [
                str(item['material_id']),
                '"%s"' % item['source_place'],
                str(item['source_rate'])
            ]
            value = ', '.join(value)
            values.append('(%s)' % value)

        sql = 'INSERT INTO t_material_source ( material_id, source_place, source_rate ) ' \
              'VALUES %s' % ', '.join(values)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def add_material_made(self, materials):
        cursor = self.db.cursor()

        values = []
        for item in materials:
            value = [
                str(item['material_id']),
                str(item['use_material_id']),
                str(item['use_number'])
            ]
            value = ', '.join(value)
            values.append('(%s)' % value)

        sql = 'INSERT INTO t_material_made ( material_id, use_material_id, use_number ) ' \
              'VALUES %s' % ', '.join(values)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def find_material_source(self, name):
        cursor = self.db.cursor()

        sql = 'SELECT material_id FROM t_material WHERE material_name = "%s"' % name
        sql = 'SELECT * FROM t_material_source WHERE material_id = (%s)' % sql

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def find_material_made(self, name):
        cursor = self.db.cursor()

        left_join = 'LEFT JOIN t_material m ON t.use_material_id = m.material_id'

        sql = 'SELECT material_id FROM t_material WHERE material_name = "%s"' % name
        sql = 'SELECT m.material_name, t.use_number FROM t_material_made t %s ' \
              'WHERE t.material_id = (%s)' % (left_join, sql)

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def truncate_all(self):
        sql = [
            'TRUNCATE t_material',
            'TRUNCATE t_material_made',
            'TRUNCATE t_material_source',
            'TRUNCATE t_operator',
            'TRUNCATE t_operator_evolve_costs',
            'TRUNCATE t_operator_skill',
            'TRUNCATE t_operator_skill_mastery_costs'
        ]
        for item in sql:
            cursor = self.db.cursor()
            self.db.ping(reconnect=True)
            cursor.execute(item)
