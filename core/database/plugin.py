from amiyabot.database import *
from core.database import config, is_mysql
from typing import Union

db = connect_database('amiya_plugin' if is_mysql else 'database/amiya_plugin.db', is_mysql, config)

class PluginBaseModel(ModelClass):
    class Meta:
        database = db
        
@table
class PluginConfiguration(PluginBaseModel):
    plugin_id: str = CharField()
    channel_id: str = CharField(null=True)
    json_config: Union[TextField, str] = TextField()
    version: str = CharField()

    class Meta:
        primary_key = CompositeKey('plugin_id', 'channel_id')