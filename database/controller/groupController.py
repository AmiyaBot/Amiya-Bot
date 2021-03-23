from database.sqlCombiner import Mysql, Formula, Where


class Group:
    def __init__(self, db: Mysql):
        self.db = db

    def set_status(self, group, status, sleep_time):
        self.db.insert(
            table='t_group',
            data={
                'group_id': group,
                'sleep_time': sleep_time,
                'active': status
            },
            update={
                'sleep_time': sleep_time,
                'active': status
            }
        )

    def get_status(self, group):
        res = self.db.select('t_group',
                             where=Where({
                                 'group_id': group
                             }),
                             fetchone=True)
        return res
