import os

from typing import List, Union
from amiyabot import MultipleAccounts, PluginInstance, log
from .customPluginInstance import AmiyaBotPluginInstance, LazyLoadPluginInstance


async def load_plugins(bot: MultipleAccounts):
    plugins: List[Union[PluginInstance, AmiyaBotPluginInstance]] = []

    for root, dirs, files in os.walk('plugins'):
        for file in files:
            if file.endswith('.zip'):
                try:
                    res = bot.load_plugin(os.path.join(root, file), extract_plugin=True)
                    if res:
                        plugins.append(res)
                        log.info(f'plugin loaded: {file}')
                except Exception as e:
                    log.error(e, f'plugin load error({file}):')
        break

    count = 0
    for item in sorted(plugins, key=lambda n: n.priority, reverse=True):
        try:
            res = bot.install_plugin(item)
            if res:
                count += 1
        except Exception as e:
            log.error(e, f'plugin install error({item.plugin_id}):')

    # 然后对所有插件执行懒加载（如果有的话）
    for plugin_id, item in bot.plugins.items():
        if isinstance(item, LazyLoadPluginInstance):
            item.load()

    if count:
        log.info(f'successfully installed {count} plugin(s).')
