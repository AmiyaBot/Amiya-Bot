from database.sqlCombiner import Mysql, Formula, Where


class Operator:
    def __init__(self, db: Mysql):
        self.db = db

    def add_operator(self, data):
        self.db.batch_insert('t_operator', data=data)

    def add_operator_detail(self, data):
        self.db.batch_insert('t_operator_detail', data=data)

    def add_operator_evolve_costs(self, data):
        self.db.batch_insert('t_operator_evolve_costs', data=data)

    def add_operator_skill(self, data):
        self.db.batch_insert('t_operator_skill', data=data)

    def add_operator_skill_mastery_costs(self, data):
        self.db.batch_insert('t_operator_skill_mastery_costs', data=data)

    def add_operator_skill_description(self, data):
        self.db.batch_insert('t_operator_skill_description', data=data)

    def add_operator_tags_relation(self, data):
        self.db.batch_insert('t_operator_tags_relation', data=data)

    def add_operator_voice(self, data):
        self.db.batch_insert('t_operator_voice', data=data)

    def add_operator_stories(self, data):
        self.db.batch_insert('t_operator_stories', data=data)

    def add_operator_talents(self, data):
        self.db.batch_insert('t_operator_talents', data=data)

    def get_operator_id(self, operator_no='', operator_name=''):
        res = self.db.select('t_operator', where=Where({
            'operator_no': operator_no,
            'operator_name': operator_name
        }, operator='OR'), fetchone=True)

        return res['operator_id'] if res else None

    def get_skill_id(self, skill_no, operator_id):
        res = self.db.select('t_operator_skill', where=Where({
            'skill_no': skill_no,
            'operator_id': operator_id
        }), fetchone=True)

        return res['skill_id'] if res else None

    def get_all_operator(self, names: list = None):
        if names:
            return self.db.select('t_operator', where=Where({
                'operator_name': ['in', Formula('("%s")' % '", "'.join(names))]
            }))
        return self.db.select('t_operator')

    def get_gacha_operator(self, limit=0, extra=None):
        return self.db.select('t_operator', where=Where({
            'limit': Where({
                'available': 1,
                'in_limit': ['in', Formula('(%d, 0)' % limit)]
            }),
            'operator_name': ['in', Formula('("%s")' % '", "'.join(extra or []))]
        }, operator='OR'))

    def get_all_operator_tags(self):
        return self.db.select('t_operator_tags_relation')

    def get_all_operator_skill(self):
        return self.db.select('t_operator_skill')

    def get_operator_skill_by_name(self, skill_name):

        sql = 'SELECT s.skill_index, o.operator_name FROM t_operator_skill s ' \
              'LEFT JOIN t_operator o ON o.operator_id = s.operator_id ' \
              'WHERE s.skill_name LIKE "%{name}%"'.format(name=skill_name)

        return self.db.select(sql=sql, fields=['skill_index', 'operator_name'])

    def get_all_stories_title(self):
        return self.db.select('t_operator_stories', sql='SELECT * FROM t_operator_stories GROUP BY story_title')

    def find_operator_evolve_costs(self, name, level):

        sql = 'SELECT operator_id FROM t_operator WHERE operator_name = "%s"' % name
        sql = 'SELECT m.material_name, m.material_icon, o.use_number FROM t_operator_evolve_costs o ' \
              'LEFT JOIN t_material m ON m.material_id = o.use_material_id ' \
              'WHERE o.evolve_level = %d AND o.operator_id in (%s)' % (level, sql)

        return self.db.select(sql=sql, fields=['material_name', 'material_icon', 'use_number'])

    def find_operator_skill_mastery_costs(self, name, level, index=0):
        field = ', '.join([
            's.skill_name',
            's.skill_index',
            's.skill_icon',
            'm.material_name',
            'm.material_icon',
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

        return self.db.select(sql=sql, fields=[
            'skill_name',
            'skill_index',
            'skill_icon',
            'material_name',
            'material_icon',
            'use_number',
            'mastery_level'
        ])

    def find_operator_skill_description(self, name, level, index=0):
        field = ', '.join([
            's.skill_name',
            's.skill_index',
            's.skill_icon',
            'd.skill_type',
            'd.sp_type',
            'd.sp_init',
            'd.sp_cost',
            'd.duration',
            'd.description',
            'd.max_charge'
        ])
        left_join = ' '.join([
            'LEFT JOIN t_operator_skill s ON s.skill_id = d.skill_id'
        ])

        sql = 'SELECT operator_id FROM t_operator WHERE operator_name = "%s"' % name
        sql = 'SELECT skill_id FROM t_operator_skill WHERE operator_id IN (%s)' % sql
        sql = 'SELECT %s FROM t_operator_skill_description d %s ' \
              'WHERE d.skill_level = %d AND d.skill_id IN (%s)' % (field, left_join, level, sql)

        if index > 0:
            sql += ' AND s.skill_index = %d' % index

        return self.db.select(sql=sql, fields=[
            'skill_name',
            'skill_index',
            'skill_icon',
            'skill_type',
            'sp_type',
            'sp_init',
            'sp_cost',
            'duration',
            'description',
            'max_charge'
        ])

    def find_operator_tags_by_tags(self, tags, min_rarity=1, max_rarity=6):

        where = []
        for item in tags:
            where.append('operator_tags = "%s"' % item)

        sql = 'SELECT * FROM t_operator_tags_relation WHERE ( %s ) ' \
              'AND operator_rarity >= %d ' \
              'AND operator_rarity <= %d ' \
              'ORDER BY operator_rarity DESC' % (' OR '.join(where), min_rarity, max_rarity)

        return self.db.select('t_operator_tags_relation', sql=sql)

    def find_operator_stories(self, name, title):
        sql = 'SELECT os.story_text FROM t_operator o ' \
              'LEFT JOIN t_operator_stories os on o.operator_id = os.operator_id ' \
              'WHERE o.operator_name = "%s" and os.story_title = "%s"' % (name, title)

        return self.db.select(sql=sql, fields=['story_text'], fetchone=True)

    def find_operator_voice(self, operator_name, title):
        return self.db.select('t_operator_voice', where=Where({
            'operator_id': self.get_operator_id(operator_name=operator_name),
            'voice_title': title
        }), fetchone=True)

    def create_tags_file(self, path='resource/tags.txt'):
        tags_list = ['资深', '高资', '高级资深']

        for item in self.get_all_operator_tags():
            if item['operator_tags'] not in tags_list:
                tags_list.append(item['operator_tags'])

        with open(path, mode='w+', encoding='utf-8') as file:
            file.write('\n'.join([item + ' 100 n' for item in tags_list]))

        return path

    def delete_all_data(self):
        tables = [
            't_operator',
            't_operator_detail',
            't_operator_evolve_costs',
            't_operator_skill',
            't_operator_skill_description',
            't_operator_skill_mastery_costs',
            't_operator_stories',
            't_operator_tags_relation',
            't_operator_talents',
            't_operator_voice'
        ]
        for item in tables:
            self.db.truncate(item)
