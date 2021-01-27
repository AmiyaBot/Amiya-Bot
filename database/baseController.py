import json
import pymysql

from .sqlCombiner import Mysql

from .controller.userController import User
from .controller.groupController import Group
from .controller.remindController import Remind
from .controller.messageController import Message
from .controller.materialController import Material
from .controller.operatorController import Operator
from .controller.functionController import Function
from .controller.resourceController import Resource


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
