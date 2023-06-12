import os
import copy
import shutil

from typing import List
from amiyabot.network.download import download_async
from core import app, bot
from core.util import check_file_content
from core.customPluginInstance.amiyaBotPluginInstance import AmiyaBotPluginInstance
from core.database.plugin import PluginConfiguration

from .__model__ import BaseModel


class GetConfigModel(BaseModel):
    plugin_id: str


class SetConfigModel(BaseModel):
    plugin_id: str
    config_json: str
    channel_id: str = None


class DelConfigModel(BaseModel):
    plugin_id: str
    channel_id: str


class InstallModel(BaseModel):
    url: str
    packageName: str


class UpgradeModel(BaseModel):
    url: str
    packageName: str
    plugin_id: str


class UninstallModel(BaseModel):
    plugin_id: str


class ReloadModel(BaseModel):
    plugin_id: str
    force: bool = False


@app.controller
class Plugin:
    @app.route(method='get')
    async def get_installed_plugin(self):
        res = []

        for _, item in bot.plugins.items():
            logo = ''
            if item.path:
                item_path = item.path[-1]
                logo = '/' + os.path.relpath(os.path.join(item_path, 'logo.png')).replace('\\', '/')

            res.append({
                'name': item.name,
                'version': item.version,
                'plugin_id': item.plugin_id,
                'plugin_type': item.plugin_type,
                'description': item.description,
                'document': check_file_content(item.document),
                'instruction': check_file_content(item.instruction) if hasattr(item, 'instruction') else '',
                'logo': logo,
                'allow_config': isinstance(item, AmiyaBotPluginInstance)
            })

        return app.response(res)

    @app.route()
    async def get_plugin_default_config(self, data: GetConfigModel):
        plugin = bot.plugins.get(data.plugin_id)
        if not plugin:
            return app.response(code=500, message='未安装该插件')

        if isinstance(plugin, AmiyaBotPluginInstance):
            return app.response(
                plugin.get_config_defaults()
            )

        return app.response()

    @app.route()
    async def get_plugin_config(self, data: GetConfigModel):
        plugin = bot.plugins.get(data.plugin_id)
        if not plugin:
            return app.response(code=500, message='未安装该插件')

        configs: List[PluginConfiguration] = PluginConfiguration.select().where(
            PluginConfiguration.plugin_id == plugin.plugin_id
        )

        config_dict = {
            item.channel_id: item.json_config
            for item in configs
        }

        return app.response(config_dict)

    @app.route()
    async def del_plugin_config(self, data: DelConfigModel):
        PluginConfiguration.delete().where(
            PluginConfiguration.plugin_id == data.plugin_id,
            PluginConfiguration.channel_id == data.channel_id
        ).execute()

        return app.response()

    @app.route()
    async def set_plugin_config(self, data: SetConfigModel):
        plugin = bot.plugins.get(data.plugin_id)
        if not plugin:
            return app.response(code=500, message='未安装该插件')

        config: PluginConfiguration = PluginConfiguration.get_or_none(
            plugin_id=plugin.plugin_id,
            channel_id=data.channel_id
        )

        if not config:
            PluginConfiguration.create(plugin_id=plugin.plugin_id,
                                       channel_id=data.channel_id,
                                       json_config=data.config_json,
                                       version=plugin.version)
        else:
            config.version = plugin.version
            config.json_config = data.config_json
            config.save()

        return app.response(message='配置已保存')

    @app.route()
    async def install_plugin(self, data: InstallModel):
        res = await download_async(data.url)
        if res:
            plugin = f'plugins/{data.packageName}'
            with open(plugin, mode='wb+') as src:
                src.write(res)

            if bot.install_plugin(plugin, extract_plugin=True):
                return app.response(message='插件安装成功')
            else:
                return app.response(code=500, message='插件安装失败')

        return app.response(code=500, message='插件下载失败，请检查网络连接。')

    @app.route()
    async def upgrade_plugin(self, data: UpgradeModel):
        res = await download_async(data.url)
        if res:
            plugin = f'plugins/{data.packageName}'
            with open(plugin, mode='wb+') as src:
                src.write(res)

            # 卸载插件
            old_plugin_path = copy.deepcopy(bot.plugins[data.plugin_id].path)
            bot.uninstall_plugin(data.plugin_id)

            if bot.install_plugin(plugin, extract_plugin=True):
                # 删除旧插件
                for item in old_plugin_path:
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                    else:
                        os.remove(item)
                return app.response(message='插件更新成功')
            else:
                # 恢复旧插件
                os.remove(plugin)
                bot.install_plugin(old_plugin_path[0], extract_plugin=True)
                return app.response(code=500, message='插件更新失败')

        return app.response(code=500, message='插件下载失败，请检查网络连接。')

    @app.route()
    async def uninstall_plugin(self, data: UninstallModel):
        bot.uninstall_plugin(data.plugin_id, remove=True)

        return app.response(message='插件卸载成功')

    @app.route()
    async def reload_plugin(self, data: ReloadModel):
        bot.reload_plugin(data.plugin_id, force=data.force)

        return app.response(message='插件重载成功')
