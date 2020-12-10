class Operator:
    def __init__(self, db):
        self.db = db

    def get_all_operator(self):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_operator'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def get_gacha_operator(self, limit=None):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_operator WHERE available = 1 AND in_limit = 0'

        if limit is not None:
            sql += ' OR operator_name IN ("%s")' % '", "'.join(limit)

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def add_operator(self, operators):
        cursor = self.db.cursor()

        values = []
        for item in operators:
            value = [
                '"%s"' % item['operator_name'],
                str(item['operator_rarity']),
                str(item['operator_class']),
                str(item['available']),
                str(item['in_limit'])
            ]
            value = ', '.join(value)
            values.append('(%s)' % value)

        sql = 'INSERT INTO t_operator ( operator_name, operator_rarity, operator_class, available, in_limit ) ' \
              'VALUES %s' % ', '.join(values)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def add_operator_evolve_costs(self, operators):
        cursor = self.db.cursor()

        values = []
        for item in operators:
            value = [
                str(item['operator_id']),
                str(item['evolve_level']),
                str(item['use_material_id']),
                str(item['use_number'])
            ]
            value = ', '.join(value)
            values.append('(%s)' % value)

        sql = 'INSERT INTO t_operator_evolve_costs ( operator_id, evolve_level, use_material_id, use_number ) ' \
              'VALUES %s' % ', '.join(values)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def find_operator_evolve_costs(self, name, level):
        cursor = self.db.cursor()

        sql = 'SELECT operator_id FROM t_operator WHERE operator_name = "%s"' % name
        sql = 'SELECT m.material_name, o.use_number FROM t_operator_evolve_costs o ' \
              'LEFT JOIN t_material m ON m.material_id = o.use_material_id ' \
              'WHERE o.evolve_level = %d AND o.operator_id = (%s)' % (level, sql)

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def get_all_operator_skill(self):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_operator_skill'

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def get_operator_skill_by_name(self, skill_name):
        cursor = self.db.cursor()

        sql = 'SELECT s.*, o.operator_name FROM t_operator_skill s ' \
              'LEFT JOIN t_operator o ON o.operator_id = s.operator_id WHERE s.skill_name = "%s"' % skill_name

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def add_operator_skill(self, operators):
        cursor = self.db.cursor()

        values = []
        for item in operators:
            value = [
                str(item['operator_id']),
                str(item['skill_index']),
                '"%s"' % item['skill_name']
            ]
            value = ', '.join(value)
            values.append('(%s)' % value)

        sql = 'INSERT INTO t_operator_skill ( operator_id, skill_index, skill_name ) ' \
              'VALUES %s' % ', '.join(values)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def add_operator_skill_mastery_costs(self, operators):
        cursor = self.db.cursor()

        values = []
        for item in operators:
            value = [
                str(item['skill_id']),
                str(item['mastery_level']),
                str(item['use_material_id']),
                str(item['use_number'])
            ]
            value = ', '.join(value)
            values.append('(%s)' % value)

        sql = 'INSERT INTO t_operator_skill_mastery_costs ( skill_id, mastery_level, use_material_id, use_number ) ' \
              'VALUES %s' % ', '.join(values)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def find_operator_skill_mastery_costs(self, name, level, index=0):
        cursor = self.db.cursor()

        field = ', '.join([
            's.skill_name',
            's.skill_index',
            'm.material_name',
            'o.use_number',
            'o.mastery_level'
        ])
        left_join = ' '.join([
            'LEFT JOIN t_material m ON m.material_id = o.use_material_id',
            'LEFT JOIN t_operator_skill s ON s.skill_id = o.skill_id'
        ])

        sql = 'SELECT operator_id FROM t_operator WHERE operator_name = "%s"' % name
        sql = 'SELECT skill_id FROM t_operator_skill WHERE operator_id IN (%s)' % sql
        sql = 'SELECT %s FROM t_operator_skill_mastery_costs o %s ' \
              'WHERE o.mastery_level = %d AND o.skill_id IN (%s)' % (field, left_join, level, sql)

        if index > 0:
            sql += ' AND s.skill_index = %d' % index

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res
