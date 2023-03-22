import json
import jsonschema

from typing import Optional, Union
from core.database.plugin import PluginConfiguration
from amiyabot import PluginInstance, log

JSON_VALUE_TYPE = Optional[Union[bool, str, int, float, dict, list]]
CONFIG_TYPE = Optional[Union[str, dict]]


class AmiyaBotPluginInstance(PluginInstance):
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
        super().__init__(name, version, plugin_id,
                         plugin_type, description, document)

        self.__channel_config_default = self.__get_obj_from_str(channel_config_default)
        self.__channel_config_schema = self.__get_obj_from_str(channel_config_schema)
        self.__global_config_default = self.__get_obj_from_str(global_config_default)
        self.__global_config_schema = self.__get_obj_from_str(global_config_schema)

        # 提供 Template 则立即执行校验
        if self.__channel_config_schema is not None:
            if self.__channel_config_default is None:
                raise ValueError(
                    'If you provide schema, you must also provide default.')
            # 立即校验 JsonSchema 是否符合
            try:
                jsonschema.validate(
                    instance=self.__channel_config_default, schema=self.__channel_config_schema)
            except jsonschema.ValidationError as e:
                raise ValueError('Your json default does not fit your schema.')

        if self.__global_config_schema is not None:
            if self.__global_config_default is None:
                raise ValueError(
                    'If you provide schema, you must also provide default.')
            # 立即校验 JsonSchema 是否符合
            try:
                jsonschema.validate(
                    instance=self.__global_config_default, schema=self.__global_config_schema)
            except jsonschema.ValidationError as e:
                raise ValueError('Your json default does not fit your schema.')

    # 同时提供 LazyLoadPluginInstance 的功能
    def load(self):
        ...

    def get_config_defaults(self):
        return {
            'channel_config_default': json.dumps(self.__channel_config_default),
            'channel_config_schema': json.dumps(self.__channel_config_schema),
            'global_config_default': json.dumps(self.__global_config_default),
            'global_config_schema': json.dumps(self.__global_config_schema),
        }

    @staticmethod
    def __get_obj_from_str(json_input: CONFIG_TYPE) -> CONFIG_TYPE:
        if json_input is None:
            return None

        if type(json_input) not in (str, dict, list):
            raise ConfigTypeError(json_input)

        # 文本 > 路径 > 对象 ==> 对象
        if isinstance(json_input, str):
            try:
                ret_val = json.loads(json_input)
                if not isinstance(ret_val, dict):
                    raise ConfigTypeError(json_input)
                return ret_val
            except json.JSONDecodeError:
                pass

        if isinstance(json_input, str):
            try:
                with open(json_input, 'r') as f:
                    ret_val = json.load(f)
                    if not isinstance(ret_val, dict):
                        raise ConfigTypeError(json_input)
                    return ret_val
            except (TypeError, FileNotFoundError):
                pass

        if not isinstance(json_input, dict):
            raise ConfigTypeError(json_input)

        return json_input

    def __get_channel_config(self, channel_id: str) -> dict:
        if channel_id is None or channel_id == '0':
            raise ValueError('Try set channel config with None channel id!')

        conf_str = PluginConfiguration.get_or_none(
            plugin_id=self.plugin_id, channel_id=channel_id)

        if conf_str is None:
            if self.__channel_config_default is not None:
                return self.__channel_config_default
            return {}

        try:
            return json.loads(conf_str.json_config)
        except json.JSONDecodeError:
            raise ValueError('The config in database is not a valid json.')

    def __set_channel_config(self, channel_id: str, config_value: dict):
        if channel_id is None or channel_id == '0':
            raise ValueError('Try set channel config with None channel id!')

        conf_str = PluginConfiguration.get_or_none(
            plugin_id=self.plugin_id, channel_id=channel_id)

        if conf_str is None:
            PluginConfiguration.create(
                plugin_id=self.plugin_id,
                channel_id=channel_id,
                json_config=json.dumps(config_value),
                version=self.version
            )
            log.info(f'{self.plugin_id}: Config Insert!')
        else:
            conf_str.json_config = json.dumps(config_value)
            conf_str.version = self.version
            conf_str.save()
            log.info(f'{self.plugin_id}: Config Update!')

    def __get_global_config(self) -> dict:
        conf_str = PluginConfiguration.get_or_none(
            plugin_id=self.plugin_id, channel_id='0')

        if conf_str is None:
            if self.__global_config_default is not None:
                return self.__global_config_default
            return {}

        try:
            return json.loads(conf_str.json_config)
        except json.JSONDecodeError:
            raise ValueError('The config in database is not a valid json.')

    def __set_global_config(self, config_value: dict):
        conf_str = PluginConfiguration.get_or_none(
            plugin_id=self.plugin_id, channel_id='0')

        if conf_str is None:
            PluginConfiguration.create(
                plugin_id=self.plugin_id,
                channel_id='0',
                json_config=json.dumps(config_value),
                version=self.version
            )
            log.info(f'{self.plugin_id}: Config Insert!')
        else:
            conf_str.json_config = json.dumps(config_value)
            conf_str.version = self.version
            conf_str.save()
            log.info(f'{self.plugin_id}: Config Update!')

    def get_config(self, channel_id, config_name) -> JSON_VALUE_TYPE:
        if channel_id and len(str(channel_id).strip()) > 0:
            json_config = self.__get_channel_config(str(channel_id))
            # 注意这里要判断 None，因为界面上如果用户不填写值，界面会将值设置为 null 而不是缺失该元素，对应到 Python 这边就是 None。
            if config_name in json_config.keys() and json_config[config_name] is not None:
                return json_config[config_name]

        json_config = self.__get_global_config()
        if config_name in json_config.keys() and json_config[config_name] is not None:
            return json_config[config_name]

        return None

    # 这里确实是期望一个 value，因为 json 的 value 既可以是基本类型也可以是 dict 类型。
    def set_config(self, channel_id: str, config_name: str, config_value: JSON_VALUE_TYPE):
        if channel_id and len(str(channel_id).strip()) > 0:
            json_config = self.__get_channel_config(str(channel_id))
        else:
            json_config = self.__get_global_config()

        json_config[config_name] = config_value

        # 如果 channel_id 为 None，则保存到全局配置
        if not channel_id:
            self.__set_global_config(json_config)
        else:
            self.__set_channel_config(str(channel_id), json_config)

        # 返回 self 以供链式调用
        return self


class ConfigTypeError(TypeError):
    def __init__(self, value):
        self.value_type = type(value)

    def __str__(self):
        return f'The Config value must be str (as json string or filename), dict, not {self.value_type}.'
