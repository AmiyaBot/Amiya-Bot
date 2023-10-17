import os
import json

from typing import Dict, Union, Optional
from amiyabot import MultipleAccounts, PluginInstance, log
from amiyabot.network.download import download_async
from amiyabot.network.httpRequests import http_requests
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
                    res = await self.load_plugin_file(os.path.join(root, file))
                    if res:
                        self.plugins[res.plugin_id] = res
            break

        # 检查依赖
        self.plugins = await self.check_requirements(self.plugins)

        log.info(f'loaded {len(self.plugins.keys())} plugin(s).')

        return await self.install_loaded_plugins()

    async def load_plugin_file(self, file: str) -> PLUGIN:
        async with log.catch(f'plugin load error({os.path.basename(file)}):'):
            res = self.bot.load_plugin(file, extract_plugin=True)
            if res:
                return res

    async def install_loaded_plugins(self):
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

        return count

    async def check_requirements(self, plugins: PLUGINS_MAP, exists_plugins: Optional[PLUGINS_MAP] = None):
        final_res: PLUGINS_MAP = {}

        for pid, item in plugins.items():
            allow_install = True

            if isinstance(item, AmiyaBotPluginInstance) and item.requirements:
                for req in item.requirements:
                    if req.plugin_id == item.plugin_id:
                        continue

                    # 本地已存在此依赖插件
                    if req.plugin_id in {**(exists_plugins or plugins), **final_res}:
                        # 本地的依赖版本不匹配，则不安装此插件
                        if req.version and req.version != plugins[req.plugin_id].version:
                            allow_install = False
                            log.error(
                                f'can not install plugin "{item.plugin_id}@{item.version}" '
                                f'because it requires "{req.plugin_id}@{req.version}", '
                                f'but "{req.plugin_id}@{plugins[req.plugin_id].version}" already exists.'
                            )
                        continue

                    # 本地不存在依赖，则从远端寻找依赖插件
                    req_plugins = await self.find_plugin_from_remote(req)
                    if req_plugins:
                        final_res = {**final_res, **req_plugins}
                    else:
                        # 如果远端无法找到依赖，则不安装此插件
                        allow_install = False
                        require = f'{req.plugin_id}@{req.version}' if req.version else req.plugin_id
                        log.error(
                            f'can not install plugin "{item.plugin_id}@{item.version}" '
                            f'because it requires "{require}", but not found from remote.'
                        )

            if allow_install:
                final_res[pid] = item

        return final_res

    async def find_plugin_from_remote(self, req: Requirement):
        req_plugins: PLUGINS_MAP = {}

        async def download_and_load(url):
            filename = os.path.basename(url)

            log.info(f'downloading plugin: {filename}')

            download_res = await download_async(url)
            if download_res:
                with open(f'plugins/{filename}', mode='wb') as plugin_file:
                    plugin_file.write(download_res)

                load_res = await self.load_plugin_file(f'plugins/{filename}')
                if load_res:
                    req_plugins[req.plugin_id] = load_res

        try:
            if req.official:
                # 官方插件从 cos 寻找依赖插件
                cos_url = f'{remote_config.remote.cos}/plugins/official/plugins.json'

                res = await http_requests.get(cos_url)
                if not res:
                    return req_plugins

                cos_plugins = {
                    item['plugin_id']: remote_config.remote.cos
                    + '/plugins/official/{plugin_id}-{version}.zip'.format(**item)
                    for item in json.loads(res)
                }

                if req.plugin_id in cos_plugins:
                    await download_and_load(cos_plugins[req.plugin_id])

            else:
                # 从插件服务寻找依赖插件
                req_url = f'{remote_config.remote.plugin}/getPluginRelease?plugin_id={req.plugin_id}'
                if req.version:
                    req_url += f'&version={req.version}'

                res = await http_requests.get(req_url)
                if not res:
                    return req_plugins

                res_data = json.loads(res)
                if res_data['code'] == 200:
                    await download_and_load(
                        f'{remote_config.remote.cos}/plugins/custom/{req.plugin_id}/' + res_data['data']['file'],
                    )

        except Exception as e:
            log.error(e, desc='plugin download error:')

        # 检查依赖的依赖
        return await self.check_requirements(req_plugins, {**self.plugins, **req_plugins})
