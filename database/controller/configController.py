from database.sqlCombiner import Mysql, Formula, Where


class Config:
    def __init__(self, db: Mysql):
        self.db = db

    def get_config(self, name, keyword, fetchone=False):
        return self.db.select('t_config_amiya', where=Where({
            'config_name': name,
            'config_keyword': keyword
        }), fetchone=fetchone)

    def get_amiya_name(self):
        return [
            self.get_config('amiya_name', 'good_name', True)['config_values'].split(','),
            self.get_config('amiya_name', 'bad_name', True)['config_values'].split(',')
        ]

    def get_amiya_keyword(self):
        return {
            'goodWords': self.get_config('amiya_keyword', 'good_word', True)['config_values'].split(','),
            'badWords': self.get_config('amiya_keyword', 'bad_word', True)['config_values'].split(',')
        }

    def get_amiya_talk(self):
        return [
            [item['config_values'] for item in self.get_config('amiya_touch', 'reply1')],
            [item['config_values'] for item in self.get_config('amiya_touch', 'reply2')]
        ]

    def get_operator_gacha_config(self, group='limit'):
        limit_operator = self.db.select(
            't_operator_gacha_config',
            where=Where({
                'operator_type': ['in', Formula('(0, 1)')] if group == 'limit' else ['>', '1']
            })
        )
        return [item['operator_name'] for item in limit_operator]
