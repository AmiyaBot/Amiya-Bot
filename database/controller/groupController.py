from database.sqlCombiner import Mysql, Calc, Where


class Group:
    def __init__(self, db: Mysql):
        self.db = db
