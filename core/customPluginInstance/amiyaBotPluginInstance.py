import os
import json
import jsonschema

from typing import Optional, Union
from core.database.plugin import PluginConfiguration
from core.util import read_yaml

from .lazyLoadPluginInstance import LazyLoadPluginInstance

JSON_VALUE_TYPE = Optional[Union[bool, str, int, float, dict, list]]
CONFIG_TYPE = Optional[Union[str, dict]]

global_config_channel_key = ''


class AmiyaBotPluginInstance(LazyLoadPluginInstance):
    def __init__(self,
                 name: str,
                 version: str,
                 plugin_id: str,
                 plugin_type: str = None,
                 description: str = None,
                 document: str = None,
                 channel_config_default: CONFIG_TYPE = None,
                 channel_config_schema: CONFIG_TYPE = None,
                 global_config_default: CONFIG_TYPE = None,
                 global_config_schema: CONFIG_TYPE = None):

        super().__init__(name,
                         version,
                         plugin_id,
                         plugin_type,
                         description,
                         document)

        self.__channel_config_default = self.__parse_to_json(channel_config_default)
        self.__channel_config_schema = self.__parse_to_json(channel_config_schema)
        self.__global_config_default = self.__parse_to_json(global_config_default)
        self.__global_config_schema = self.__parse_to_json(global_config_schema)

        self.validate_schema()

        # 如果是插件初次安装初次加载，那么立刻应用global_default

        if self.__global_config_default is not None:
            global_conf = self.__get_global_config()
            if global_conf is None:
                self.__set_global_config(self.__global_config_default)

    def validate_schema(self):
        for default, schema in (
            (self.__channel_config_default, self.__channel_config_schema),
            (self.__global_config_default, self.__global_config_schema)
        ):
            # 提供 Template 则立即执行校验
            if schema is not None:
                if default is None:
                    raise ValueError('If you provide schema, you must also provide default.')

                # 立即校验 JsonSchema 是否符合
                try:
                    jsonschema.validate(
                        instance=default,
                        schema=schema
                    )
                except jsonschema.ValidationError as e:
                    raise ValueError('Your json default does not fit your schema.') from e

    def get_config_defaults(self):
        return {
            'channel_config_default': json.dumps(self.__channel_config_default),
            'channel_config_schema': json.dumps(self.__channel_config_schema),
            'global_config_default': json.dumps(self.__global_config_default),
            'global_config_schema': json.dumps(self.__global_config_schema)
        }

    @staticmethod
    def __parse_to_json(value: CONFIG_TYPE) -> CONFIG_TYPE:
        if not value:
            return None

        if isinstance(value, dict):
            return value

        if not isinstance(value, str):
            raise ConfigTypeError(value)

        try:
            res = json.loads(value)

            if not isinstance(res, dict):
                raise ConfigTypeError(value)

            return res
        except json.JSONDecodeError:
            pass

        # json 或 yaml 文件
        if os.path.exists(value):
            if value.endswith('yaml'):
                res = read_yaml(value, _dict=True, _refresh=True)
            else:
                with open(value, 'r', encoding='utf-8') as file:
                    res = json.load(file)

            if not isinstance(res, dict):
                raise ConfigTypeError(value)

            return res

    def __get_channel_config(self, channel_id: str) -> dict:
        if not channel_id or channel_id == global_config_channel_key:
            raise ValueError('Try set channel config with None channel id!')

        conf_str: PluginConfiguration = PluginConfiguration.get_or_none(plugin_id=self.plugin_id, channel_id=channel_id)

        if not conf_str:
            return self.__channel_config_default or {}

        try:
            return json.loads(conf_str.json_config)
        except json.JSONDecodeError:
            raise ValueError('The config in database is not a valid json.')

    def __set_channel_config(self, channel_id: str, config_value: dict):
        if not channel_id or channel_id == global_config_channel_key:
            raise ValueError('Try set channel config with None channel id!')

        conf_str: PluginConfiguration = PluginConfiguration.get_or_none(plugin_id=self.plugin_id, channel_id=channel_id)

        if not conf_str:
            PluginConfiguration.create(
                plugin_id=self.plugin_id,
                channel_id=channel_id,
                json_config=json.dumps(config_value),
                version=self.version
            )
        else:
            conf_str.json_config = json.dumps(config_value)
            conf_str.version = self.version
            conf_str.save()

    def __get_global_config(self) -> dict:
        conf_str: PluginConfiguration = PluginConfiguration.get_or_none(plugin_id=self.plugin_id,
                                                                        channel_id=global_config_channel_key)

        if not conf_str:
            return self.__global_config_default or {}

        try:
            return json.loads(conf_str.json_config)
        except json.JSONDecodeError:
            raise ValueError('The config in database is not a valid json.')

    def __set_global_config(self, config_value: dict):
        conf_str: PluginConfiguration = PluginConfiguration.get_or_none(plugin_id=self.plugin_id,
                                                                        channel_id=global_config_channel_key)

        if not conf_str:
            PluginConfiguration.create(
                plugin_id=self.plugin_id,
                json_config=json.dumps(config_value),
                version=self.version
            )
        else:
            conf_str.json_config = json.dumps(config_value)
            conf_str.version = self.version
            conf_str.save()

    def get_config(self, config_name: str, channel_id: str = None) -> JSON_VALUE_TYPE:
        if channel_id and channel_id != global_config_channel_key:
            json_config = self.__get_channel_config(str(channel_id))

            # 注意这里要判断 None，因为界面上如果用户不填写值，界面会将值设置为 null 而不是缺失该元素，对应到 Python 这边就是 None。
            if config_name in json_config and json_config[config_name] is not None:
                value = json_config[config_name]

                # todo 此处是为了表明逻辑，未来这里会加入可能的诸多检查。
                # 目前，因为前端界面删除所有条目后，实际存储的是空数组/空字符串。
                # if value == []:
                #     ...

                if isinstance(value, str):
                    if value != '':
                        return value
                else:
                    return value

        json_config = self.__get_global_config()

        if config_name in json_config and json_config[config_name] is not None:
            return json_config[config_name]

        return None

    def set_config(self, config_name: str, config_value: JSON_VALUE_TYPE, channel_id: str = None):
        if channel_id and channel_id != global_config_channel_key:
            json_config = self.__get_channel_config(str(channel_id))
        else:
            json_config = self.__get_global_config()

        json_config[config_name] = config_value

        # 如果 channel_id 为 None，则保存到全局配置
        if channel_id:
            self.__set_channel_config(str(channel_id), json_config)
        else:
            self.__set_global_config(json_config)

        return self


class ConfigTypeError(TypeError):
    def __init__(self, value):
        self.value_type = type(value)

    def __str__(self):
        return f'The Config value must be str (as json string or filename), dict, not {self.value_type}.'
