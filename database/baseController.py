from database.sqlCombiner import Mysql
from database.controller.userController import User
from database.controller.groupController import Group
from database.controller.configController import Config
from database.controller.remindController import Remind
from database.controller.messageController import Message
from database.controller.materialController import Material
from database.controller.operatorController import Operator
from database.controller.functionController import Function
from database.controller.resourceController import Resource
from modules.config import get_config


class BaseController:
    def __init__(self):
        config = get_config('database')

        self.comb = Mysql(config)

        self.user = User(self.comb)
        self.group = Group(self.comb)
        self.config = Config(self.comb)
        self.remind = Remind(self.comb)
        self.message = Message(self.comb)
        self.material = Material(self.comb)
        self.operator = Operator(self.comb)
        self.function = Function(self.comb)
        self.resource = Resource(self.comb)

    def close(self):
        self.comb.close()
