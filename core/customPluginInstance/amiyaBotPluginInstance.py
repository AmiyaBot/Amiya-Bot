import os
import json
import copy
import jsonschema

from peewee import *
from typing import Optional, Union, List
from core.database.plugin import PluginConfiguration, PluginConfigurationAudit
from core.util import read_yaml
from datetime import datetime, timedelta
from core import log

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
                 priority: int = 1,
                 instruction: str = None,
                 channel_config_default: CONFIG_TYPE = None,
                 channel_config_schema: CONFIG_TYPE = None,
                 global_config_default: CONFIG_TYPE = None,
                 global_config_schema: CONFIG_TYPE = None,
                 deprecated_config_delete_days: int = 7
                 ):

        super().__init__(name,
                         version,
                         plugin_id,
                         plugin_type,
                         description,
                         document,
                         priority)

        self.instruction = instruction
        self.__channel_config_default = self.__parse_to_json(channel_config_default)
        self.__channel_config_schema = self.__parse_to_json(channel_config_schema)
        self.__global_config_default = self.__parse_to_json(global_config_default)
        self.__global_config_schema = self.__parse_to_json(global_config_schema)
        self.__deprecated_config_delete_days = deprecated_config_delete_days

        self.validate_schema()

        # 执行一个额外的验证，提供了频道配置的，必须提供全局配置
        if self.__global_config_default is None and self.__channel_config_default is not None:
            raise ValueError(
                'If you provide channel default, you must also provide global default.')

        configs: List[PluginConfiguration] = PluginConfiguration.select().where(
            PluginConfiguration.plugin_id == self.plugin_id
        )

        if self.__global_config_default is not None:
            global_conf = next(
                (config for config in configs if config.channel_id == global_config_channel_key), None)
            if global_conf is None:
                # 如果是插件初次安装初次加载，那么立刻应用global_default
                self.__set_global_config(self.__global_config_default)
                PluginConfigurationAudit.create(
                    plugin_id=self.plugin_id,
                    channel_id=global_config_channel_key,
                    audit_time=datetime.now(),
                    audit_reason='Plugin Initialize',
                    version=self.version
                )
            else:
                try:
                    global_conf_json = json.loads(global_conf.json_config)
                    # 比对版本
                    if compare_version_numbers(global_conf.version, self.version) < 0:
                        # 数据库的版本老，执行逐项更新
                        merge_extra_items(global_conf_json,
                                          self.__global_config_default)
                        self.__set_global_config(global_conf_json)
                        PluginConfigurationAudit.create(
                            plugin_id=self.plugin_id,
                            channel_id=global_config_channel_key,
                            audit_time=datetime.now(),
                            audit_reason='Plugin Upgrade',
                            version=self.version
                        )
                except json.JSONDecodeError:
                    # 数据库中数据损坏，报错并用默认值覆盖
                    log.error(
                        f'数据库中插件{self.name}({self.plugin_id})的全局配置损坏，已重置为默认值。')
                    self.__set_global_config(self.__global_config_default)

        if self.__channel_config_default is not None:
            for channel_conf in (config for config in configs if config.channel_id != global_config_channel_key):
                try:
                    channel_conf_json = json.loads(channel_conf.json_config)
                    # 比对版本
                    if compare_version_numbers(channel_conf.version, self.version) < 0:
                        # 数据库的版本老，执行逐项更新
                        merge_extra_items(channel_conf_json,
                                          self.__channel_config_default)
                        self.__set_channel_config(
                            channel_conf.channel_id, channel_conf_json)
                        PluginConfigurationAudit.create(
                            plugin_id=self.plugin_id,
                            channel_id=channel_conf.channel_id,
                            audit_time=datetime.now(),
                            audit_reason='Plugin Upgrade',
                            version=self.version
                        )
                except json.JSONDecodeError:
                    # 数据库中数据损坏，报错并用默认值覆盖
                    log.error(
                        f'数据库中插件{self.name}({self.plugin_id})的频道配置损坏，已重置为默认值。')
                    self.__set_channel_config(
                        channel_conf.channel_id, self.__channel_config_default)

        # 接下来，针对Audit执行检查
        try:
            self.deprecated_config_delete()
        except Exception as e:
            log.error(e, f"Error")

    # 如果距离插件更新已经过去天，移除既不存在于default，也不存在于Schema的配置项。
    # 然后写入Audit信息。
    def deprecated_config_delete(self):

        if self.__deprecated_config_delete_days is None or self.__deprecated_config_delete_days < 0:
            return

        max_audit_time_subquery = (PluginConfigurationAudit
                                   .select(PluginConfigurationAudit.channel_id,
                                           fn.MAX(PluginConfigurationAudit.id).alias('max_id'))
                                   .where((PluginConfigurationAudit.plugin_id == self.plugin_id) &
                                          ((PluginConfigurationAudit.audit_reason == 'Plugin Upgrade') |
                                           (
                                               PluginConfigurationAudit.audit_reason == 'Plugin Configuration Deprecated')))
                                   .group_by(PluginConfigurationAudit.channel_id))

        query = (PluginConfigurationAudit
                 .select(PluginConfigurationAudit.channel_id,
                         PluginConfigurationAudit.id,
                         PluginConfigurationAudit.audit_time,
                         PluginConfigurationAudit.audit_reason)
                 .join(max_audit_time_subquery, on=(
            (PluginConfigurationAudit.channel_id == max_audit_time_subquery.c.channel_id) &
            (PluginConfigurationAudit.id == max_audit_time_subquery.c.max_id)))
                 .where((PluginConfigurationAudit.plugin_id == self.plugin_id) &
                        (PluginConfigurationAudit.audit_reason == 'Plugin Upgrade')))

        result = [{'id': row.id,
                   'channel_id': row.channel_id,
                   'audit_time': row.audit_time,
                   'audit_reason': row.audit_reason}
                  for row in query]

        for record in result:
            channel_id = record['channel_id']
            audit_time = record['audit_time']

            if audit_time < datetime.now() - timedelta(days=self.__deprecated_config_delete_days):
                # 满足条件，需要处理

                if channel_id == global_config_channel_key:
                    log.info('全局配置的配置项需要检查并剔除老旧配置项。')
                    # 全局配置
                    cfg = self.__get_global_config()
                    if cfg is not None:
                        remove_uncommon_elements(
                            cfg, self.__global_config_default, self.__global_config_schema)
                        self.__set_global_config(cfg)
                        PluginConfigurationAudit.create(
                            plugin_id=self.plugin_id,
                            channel_id=channel_id,
                            audit_time=datetime.now(),
                            audit_reason='Plugin Configuration Deprecated',
                            version=self.version
                        )
                else:
                    log.info(f'频道{channel_id}配置的配置项需要检查并剔除老旧配置项。')
                    cfg = self.__get_channel_config(channel_id)
                    if cfg is not None:
                        remove_uncommon_elements(
                            cfg, self.__channel_config_default, self.__channel_config_schema)
                        self.__set_channel_config(channel_id, cfg)
                        PluginConfigurationAudit.create(
                            plugin_id=self.plugin_id,
                            channel_id=channel_id,
                            audit_time=datetime.now(),
                            audit_reason='Plugin Configuration Deprecated',
                            version=self.version
                        )

    def validate_schema(self):
        for default, schema in (
            (self.__channel_config_default, self.__channel_config_schema),
            (self.__global_config_default, self.__global_config_schema)
        ):
            # 提供 Template 则立即执行校验
            if schema is not None:
                if default is None:
                    raise ValueError(
                        'If you provide schema, you must also provide default.')

                # 立即校验 JsonSchema 是否符合
                try:
                    jsonschema.validate(
                        instance=default,
                        schema=schema
                    )
                except jsonschema.ValidationError as e:
                    raise ValueError(
                        'Your json default does not fit your schema.') from e

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

    def __get_channel_config(self, channel_id: str) -> Optional[dict]:
        if not channel_id or channel_id == global_config_channel_key:
            raise ValueError('Try set channel config with None channel id!')

        conf_str: PluginConfiguration = PluginConfiguration.get_or_none(
            plugin_id=self.plugin_id, channel_id=channel_id)

        if not conf_str:
            return None

        try:
            return json.loads(conf_str.json_config)
        except json.JSONDecodeError:
            raise ValueError('The config in database is not a valid json.')

    def __set_channel_config(self, channel_id: str, config_value: dict):
        if not channel_id or channel_id == global_config_channel_key:
            raise ValueError('Try set channel config with None channel id!')

        conf_str: PluginConfiguration = PluginConfiguration.get_or_none(
            plugin_id=self.plugin_id, channel_id=channel_id)

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
            return copy.deepcopy(self.__global_config_default) or {}

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
                channel_id=global_config_channel_key,
                json_config=json.dumps(config_value),
                version=self.version
            )
        else:
            conf_str.json_config = json.dumps(config_value)
            conf_str.version = self.version
            conf_str.save()

    def get_config(self, config_name: str, channel_id: str = None) -> JSON_VALUE_TYPE:

        # 开发的思路改变了，现在以GUI为准，因此，如果插件没有提供channel_default，就表示该插件不支持设置频道级别配置，直接降级。
        if self.__channel_config_default is None:

            # 没有提供频道默认配置，这表示用户压根没提供预定义文件，他就是单纯想借用一下这个功能。
            # 那么在不报错的情况下，如实的返回或者降级即可。
            if channel_id and channel_id != global_config_channel_key:
                json_config = self.__get_channel_config(str(channel_id))
                if json_config is not None:
                    if config_name in json_config:
                        return json_config[config_name]

        else:
            if channel_id and channel_id != global_config_channel_key:
                json_config = self.__get_channel_config(str(channel_id))
                if json_config is not None:
                    # 频道级别的配置存在

                    if config_name not in json_config:
                        # 这个配置项不在频道级别配置里，这不可能，因为启动时应该补过了。
                        # 通过GUI配置配置项的时候，是没法删除项的。
                        # 所以出现不存在的项要么是因为新配置加入了，但是由于某些原因没有补。
                        # 或者，可能是插件开发者在调用时传入了错误的配置项name，这种情况的话，降级即可。

                        # 检查一下 default，如果存在，就表示确实错了，
                        if config_name in self.__channel_config_default:
                            # ok, 默认配置项存在，那么就直接给出默认值。并且警告用户。
                            log.debug(
                                f'配置项{config_name}在该频道的配置项中缺失，现在返回了频道默认值')
                            return copy.deepcopy(self.__channel_config_default[config_name])

                    # 注意这里要判断 None，界面是不可能把一个配置项改成None的，因此出现None必是因为插件开发者代码中设置了None
                    # 这里发出警告并降级即可
                    elif json_config[config_name] is None:
                        log.debug(
                            f'配置项{config_name}在数据库的Json存储中缺失，现在返回了频道默认值')
                    else:
                        value = json_config[config_name]

                        # 如果这个值被判定为empty value，这就表明这个值是被前端界面设置为空的，或者插件的default给的就是空
                        # 那么这里降级是对的。
                        if not is_empty_value(value):
                            return value

        # 执行路径降级到了全局配置
        if self.__global_config_default is None:
            # 没有提供全局默认配置，这表示用户压根就没提供任何预定义文件，他就是单纯想借用一下这个功能。
            # 那么在不报错的情况下，如实的返回即可。
            json_config = self.__get_global_config()
            if json_config is not None:
                if config_name in json_config:
                    return json_config[config_name]
            return None
        else:
            json_config = self.__get_global_config()
            if json_config is not None:
                if config_name in json_config:
                    return json_config[config_name]
                else:
                    # 这个配置项不在配置里，这不可能，因为启动时应该补过了。
                    # 通过GUI配置配置项的时候，是没法删除项的。
                    # 所以出现不存在的项要么是因为新配置加入了，但是由于某些原因没有补。
                    log.debug(f'配置项{config_name}在全局配置项中缺失，现在返回了全局默认值')
                    if config_name in self.__global_config_default:
                        return copy.deepcopy(self.__global_config_default[config_name])
            return None

    def set_config(self, config_name: str, config_value: JSON_VALUE_TYPE, channel_id: str = None):
        if channel_id and channel_id != global_config_channel_key:
            json_config = self.__get_channel_config(str(channel_id))

            if json_config is None:
                if self.__channel_config_default is not None:
                    json_config = copy.deepcopy(self.__channel_config_default)
                else:
                    json_config = {}
        else:
            json_config = self.__get_global_config()

            if json_config is None:
                if self.__global_config_default is not None:
                    json_config = copy.deepcopy(self.__global_config_default)
                else:
                    json_config = {}

        json_config[config_name] = config_value

        # 如果 channel_id 为 None，则保存到全局配置
        if channel_id and channel_id != global_config_channel_key:
            self.__set_channel_config(str(channel_id), json_config)
        else:
            self.__set_global_config(json_config)

        return self


class ConfigTypeError(TypeError):
    def __init__(self, value):
        self.value_type = type(value)

    def __str__(self):
        return f'The Config value must be str (as json string or filename), dict, not {self.value_type}.'


def is_empty_value(value: JSON_VALUE_TYPE):
    """
    此处是为了表明逻辑，未来这里会加入可能的诸多检查。
    目前，因为前端界面删除所有条目后，实际存储的是空数组/空字符串。
    :param value:
    :return:
    """
    if value == []:
        return True

    if isinstance(value, str):
        if value == '':
            return True

    return False


def compare_version_numbers(version1: str, version2: str) -> int:
    # 将版本号字符串分割成数字列表，忽略空值
    version1_numbers = [int(num) for num in version1.split('.') if num]
    version2_numbers = [int(num) for num in version2.split('.') if num]

    # 计算两个版本号列表的长度差
    length_difference = len(version1_numbers) - len(version2_numbers)

    # 如果一个版本号较短，将其扩展为与较长版本号相同的长度，用0填充
    if length_difference > 0:
        version2_numbers.extend([0] * length_difference)
    elif length_difference < 0:
        version1_numbers.extend([0] * abs(length_difference))

    # 逐个比较版本号中的数字
    for num1, num2 in zip(version1_numbers, version2_numbers):
        if num1 > num2:
            return 1  # version1 大于 version2
        elif num1 < num2:
            return -1  # version1 小于 version2

    return 0  # version1 等于 version2


def merge_extra_items(source: dict, base: dict) -> dict:
    """
    将 base 中，source 没有的元素，copy 进 source。
    :param source:
    :param base:
    :return:
    """
    diff_dict = {key: copy.deepcopy(
        value) for key, value in base.items() if key not in source}
    source.update(diff_dict)
    return source


def remove_uncommon_elements(source: dict, base: dict, schema: dict) -> None:
    """
    删除 source 中所有不在 base 中的元素
    :param source:
    :param base:
    :param schema:
    :return:
    """
    if base is None:
        return

    keys_to_remove = []

    for key in source:
        if key not in base:
            keys_to_remove.append(key)

    if schema is not None:
        if 'properties' in schema.keys():
            for key in schema['properties'].keys():
                if key in keys_to_remove:
                    keys_to_remove.remove(key)

    for key in keys_to_remove:
        source.pop(key)
