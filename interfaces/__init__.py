from .dashboard import Dashboard
from .replace import Replace
from .admin import Admin
from .group import Group
from .gacha import Pool, Operator
from .user import User
from .bot import Bot
from .api import Api

controllers = [
    Dashboard,
    Operator,
    Replace,
    Admin,
    Group,
    Pool,
    User,
    Bot,
    Api,
]
