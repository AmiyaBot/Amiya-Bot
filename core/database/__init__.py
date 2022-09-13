from amiyabot.database import MysqlConfig
from core.util import read_yaml, create_dir

setting = read_yaml('config/database.yaml', _dict=True)

is_mysql = setting['mode'] == 'mysql'
config = MysqlConfig(**setting['config']) if is_mysql else None

if not is_mysql:
    create_dir('database')
