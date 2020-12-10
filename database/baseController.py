import json
import pymysql

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

        self.db = pymysql.connect(
            host=base_config['host'],
            port=base_config['port'],
            user=base_config['user'],
            password=base_config['password'],
            db=base_config['db'],
            charset='utf8',
            autocommit=1
        )
        self.user = User(self.db)
        self.group = Group(self.db)
        self.remind = Remind(self.db)
        self.message = Message(self.db)
        self.material = Material(self.db)
        self.operator = Operator(self.db)
        self.function = Function(self.db)
        self.resource = Resource(self.db)

    def close(self):
        self.db.close()
