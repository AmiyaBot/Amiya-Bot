import json
import jsonschema

from core.database.plugin import PluginConfiguration
from amiyabot import PluginInstance, log


class AmiyaBotPluginInstance(PluginInstance):
    def __init__(self,
                 name: str,
                 version: str,
                 plugin_id: str,
                 plugin_type: str = None,
                 description: str = None,
                 document: str = None,
                 channel_config_default: object = None,
                 channel_config_schema: object = None,
                 global_config_default: object = None,
                 global_config_schema: object = None):
        super().__init__(name, version, plugin_id,
                       plugin_type, description, document)

        self.__channel_config_default = self.__get_obj_from_str(
            channel_config_default)
        self.__channel_config_schema = self.__get_obj_from_str(
            channel_config_schema)
        self.__global_config_default = self.__get_obj_from_str(
            global_config_default)
        self.__global_config_schema = self.__get_obj_from_str(
            global_config_schema)

        # 提供Template则立即执行校验
        if self.__channel_config_schema is not None:
            if self.__channel_config_default is None:
                raise ValueError(
                    'If you provide schema, you must also provide default.')
            # 立即校验JsonSchema是否符合
            try:
                jsonschema.validate(
                    instance=self.__channel_config_default, schema=self.__channel_config_schema)
            except jsonschema.ValidationError as e:
                raise ValueError('Your json default does not fit your schema.')

        if self.__global_config_schema is not None:
            if self.__global_config_default is None:
                raise ValueError(
                    'If you provide schema, you must also provide default.')
            # 立即校验JsonSchema是否符合
            try:
                jsonschema.validate(
                    instance=self.__global_config_default, schema=self.__global_config_schema)
            except jsonschema.ValidationError as e:
                raise ValueError('Your json default does not fit your schema.')

    # 同时提供LazyLoadPluginInstance的功能
    def load(self): ...

    def get_config_defaults(self):
        return {
            'channel_config_default':json.dumps(self.__channel_config_default),
            'channel_config_schema':json.dumps(self.__channel_config_schema),
            'global_config_default':json.dumps(self.__global_config_default),
            'global_config_schema':json.dumps(self.__global_config_schema),
        }

    def __get_obj_from_str(self, json_input: object) -> dict:
        if json_input is None:
            return None

        # 文本>路径>对象 ==> 对象
        if isinstance(json_input, str):
            try:
                obj = json.loads(json_input)
                return obj
            except json.JSONDecodeError:
                pass
        if isinstance(json_input, str):
            try:
                with open(json_input, "r") as f:
                    obj = json.load(f)
                    return obj
            except (TypeError, FileNotFoundError):
                pass
        # 默认返回传入的对象
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

    def get_config(self, channel_id, config_name):
        if channel_id and len(str(channel_id).strip()) > 0:
            json_config = self.__get_channel_config(str(channel_id))
            # 注意这里要判断None，因为界面上如果用户不填写值，界面会将值设置为null而不是缺失该元素，对应到Python这边就是None。
            if config_name in json_config.keys() and json_config[config_name] is not None:
                return json_config[config_name]

        json_config = self.__get_global_config()
        if config_name in json_config.keys() and json_config[config_name] is not None:
            return json_config[config_name]

        return None

    # 这里确实是期望一个value，因为json的value既可以是基本类型也可以是dict类型。
    def set_config(self, channel_id: str, config_name: str, config_value: object):
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

        # 返回self以供链式调用
        return self
