from core.database.plugin import PluginConfiguration
from amiyabot import PluginInstance, log

def get_channel_config(self: PluginInstance, channel_id: str):
    if channel_id is None or channel_id == '0':
        log.error(f'{self.plugin_id}: Try get channel config with None channel id!')
        return '{}'

    conf_str = PluginConfiguration.get_or_none(plugin_id=self.plugin_id, channel_id=channel_id)

    if conf_str is None:
        # try return default
        if hasattr(self, 'default_channel_config'):
            return self.default_channel_config
        return '{}'

    return conf_str.json_config


def set_channel_config(self: PluginInstance, channel_id: str, json: str):
    if channel_id is None or channel_id == '0':
        log.error(f'{self.plugin_id}: Try set channel config with None channel id!')
        return

    data = {
        'plugin_id': self.plugin_id,
        'channel_id': channel_id,
        'json_config': json,
        'version': self.version
    }

    conf_str = PluginConfiguration.get_or_none(plugin_id=self.plugin_id, channel_id=channel_id)

    if conf_str is None:
        PluginConfiguration.create(
            plugin_id=self.plugin_id,
            channel_id=channel_id,
            json_config=json,
            version=self.version
        )
        log.info(f'{self.plugin_id}: Config Insert!')
    else:
        conf_str.json_config = json
        conf_str.version = self.version
        conf_str.save()
        log.error(f'{self.plugin_id}: Config Update!')


def get_global_config(self: PluginInstance):
    conf_str = PluginConfiguration.get_or_none(plugin_id=self.plugin_id, channel_id='0')

    if conf_str is None:
        # try return default
        if hasattr(self, 'default_global_config'):
            return self.default_global_config
        return '{}'

    return conf_str.json_config


def set_global_config(self: PluginInstance, json: str):
    conf_str = PluginConfiguration.get_or_none(plugin_id=self.plugin_id, channel_id='0')

    if conf_str is None:
        PluginConfiguration.create(
            plugin_id=self.plugin_id,
            channel_id='0',
            json_config=json,
            version=self.version
        )
        log.info('{self.plugin_id}: Config Insert!')
    else:
        conf_str.json_config = json
        conf_str.version = self.version
        conf_str.save()
        log.error(f'{self.plugin_id}: Config Update!')

PluginInstance.get_channel_config = get_channel_config
PluginInstance.set_channel_config = set_channel_config
PluginInstance.get_global_config = get_global_config
PluginInstance.set_global_config = set_global_config

del get_channel_config
del set_channel_config
del get_global_config
del set_global_config