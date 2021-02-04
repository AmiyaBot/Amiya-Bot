import json

from database.sqlCombiner import Mysql
from database.controller.userController import User
from database.controller.groupController import Group
from database.controller.remindController import Remind
from database.controller.messageController import Message
from database.controller.materialController import Material
from database.controller.operatorController import Operator
from database.controller.functionController import Function
from database.controller.resourceController import Resource


class BaseController:
    def __init__(self):
        with open('config.json') as file:
            config = json.load(file)
            base_config = config['database']

        self.comb = Mysql(base_config)

        self.user = User(self.comb)
        self.group = Group(self.comb)
        self.remind = Remind(self.comb)
        self.message = Message(self.comb)
        self.material = Material(self.comb)
        self.operator = Operator(self.comb)
        self.function = Function(self.comb)
        self.resource = Resource(self.comb)

    def close(self):
        self.comb.close()
