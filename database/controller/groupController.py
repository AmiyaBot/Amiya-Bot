from database.sqlCombiner import Mysql, Formula, Where


class Group:
    def __init__(self, db: Mysql):
        self.db = db
