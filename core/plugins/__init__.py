import os

from typing import Dict, Union
from amiyabot import MultipleAccounts, PluginInstance, log
from core.config import remote_config

from .customPluginInstance import AmiyaBotPluginInstance, Requirement


PLUGIN = Union[PluginInstance, AmiyaBotPluginInstance]
PLUGINS_MAP = Dict[str, PLUGIN]


class PluginsLoader:
    def __init__(self, bot: MultipleAccounts):
        self.bot = bot
        self.plugins: PLUGINS_MAP = {}

    async def load_local_plugins(self):
        for root, dirs, files in os.walk('plugins'):
            for file in files:
                if file.endswith('.zip'):
                    await self.load_plugin(os.path.join(root, file))
            break

        # 检查依赖
        self.plugins = await self.check_requirements(self.plugins)

        log.info(f'loaded {len(self.plugins.keys())} plugin(s).')

        await self.install_plugins()

    async def load_plugin(self, file: str):
        async with log.catch(f'plugin load error({os.path.basename(file)}):'):
            res = self.bot.load_plugin(file, extract_plugin=True)
            if res:
                self.plugins[res.plugin_id] = res

    async def install_plugins(self):
        count = 0
        for item in sorted(self.plugins.values(), key=lambda n: n.priority, reverse=True):
            try:
                res = self.bot.install_plugin(item)
                if res:
                    count += 1
            except Exception as e:
                log.error(e, f'plugin install error({item.plugin_id}):')

        # 然后对所有插件执行懒加载（如果有的话）
        for plugin_id, item in self.bot.plugins.items():
            if isinstance(item, AmiyaBotPluginInstance):
                item.load()

        if count:
            log.info(f'installed {count} plugin(s).')

    async def check_requirements(self, plugins: PLUGINS_MAP):
        final_res: PLUGINS_MAP = {}

        for pid, item in plugins.items():
            allow_install = True

            if isinstance(item, AmiyaBotPluginInstance) and item.requirements:
                for req in item.requirements:
                    if req.plugin_id == item.plugin_id:
                        continue

                    # 本地已存在此依赖插件
                    if req.plugin_id in plugins:
                        # 本地的依赖版本不匹配，则不安装此插件
                        if req.version and req.version != plugins[req.plugin_id].version:
                            allow_install = False
                        continue

                    # 本地不存在依赖，则从远端寻找依赖插件
                    req_plugins = await self.find_plugin_from_remote(req)
                    if req_plugins:
                        for req_pid, req_plugin in req_plugins.items():
                            final_res[req_pid] = req_plugin
                    else:
                        # 如果远端无法找到依赖，则不安装此插件
                        allow_install = False

            if allow_install:
                final_res[pid] = item

        return final_res

    async def find_plugin_from_remote(self, req: Requirement) -> PLUGINS_MAP:
        req_plugins: PLUGINS_MAP = {}

        url = f'{remote_config.remote.plugin}/getPluginRelease?plugin_id={req.plugin_id}'
        if req.version:
            url += f'&version={req.version}'

        print(url)

        # 检查依赖的依赖
        return await self.check_requirements(req_plugins)
