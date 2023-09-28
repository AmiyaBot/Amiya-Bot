import os

from typing import Dict, Union, Optional
from amiyabot import MultipleAccounts, PluginInstance, log
from .customPluginInstance import AmiyaBotPluginInstance


PLUGINS_MAP = Dict[str, Union[PluginInstance, AmiyaBotPluginInstance]]


async def load_local_plugins(bot: MultipleAccounts):
    plugins: PLUGINS_MAP = {}

    for root, dirs, files in os.walk('plugins'):
        for file in files:
            if file.endswith('.zip'):
                plugins.update(await load_plugin(bot, os.path.join(root, file)))
        break

    log.info(f'loaded {len(plugins.keys())} plugin(s).')

    await install_plugins(bot, plugins)


async def install_plugins(bot: MultipleAccounts, plugins: PLUGINS_MAP):
    count = 0
    for item in sorted(plugins.values(), key=lambda n: n.priority, reverse=True):
        try:
            res = bot.install_plugin(item)
            if res:
                count += 1
        except Exception as e:
            log.error(e, f'plugin install error({item.plugin_id}):')

    # 然后对所有插件执行懒加载（如果有的话）
    for plugin_id, item in bot.plugins.items():
        if isinstance(item, AmiyaBotPluginInstance):
            item.load()

    if count:
        log.info(f'installed {count} plugin(s).')


async def load_plugin(bot: MultipleAccounts, file: str, res_list: Optional[PLUGINS_MAP] = None):
    if res_list is None:
        res_list = {}

    try:
        res = bot.load_plugin(file, extract_plugin=True)
        if res:
            res_list[res.plugin_id] = res
    except Exception as e:
        log.error(e, f'plugin load error({os.path.basename(file)}):')

    return res_list
