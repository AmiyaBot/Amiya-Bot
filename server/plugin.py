import os
import base64

from amiyabot.network.download import download_async
from core import app, bot

from .__model__ import BaseModel


class InstallModel(BaseModel):
    url: str
    packageName: str


class UpgradeModel(BaseModel):
    url: str
    packageName: str
    plugin_id: str


class UninstallModel(BaseModel):
    plugin_id: str


@app.controller
class Plugin:
    @app.route(method='get')
    async def get_installed_plugin(self):
        res = []

        for _, item in bot.plugins.items():
            doc = item.document
            if os.path.isfile(doc):
                with open(doc, mode='r', encoding='utf-8') as file:
                    content = file.read()
            else:
                content = doc

            logo = ''
            if item.path:
                item_path = item.path[-1]
                logo_path = os.path.join(item_path, 'logo.png')
                if os.path.exists(logo_path):
                    with open(logo_path, mode='rb') as ico:
                        logo = 'data:image/png;base64,' + base64.b64encode(ico.read()).decode()

            res.append({
                'name': item.name,
                'version': item.version,
                'plugin_id': item.plugin_id,
                'plugin_type': item.plugin_type,
                'description': item.description,
                'document': content,
                'logo': logo
            })

        return app.response(res)

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
        return app.response(code=500, message='插件下载失败')

    @app.route()
    async def upgrade_plugin(self, data: UpgradeModel):
        res = await download_async(data.url)
        if res:
            plugin = f'plugins/{data.packageName}'
            with open(plugin, mode='wb+') as src:
                src.write(res)

            bot.uninstall_plugin(data.plugin_id, remove=True)
            if bot.install_plugin(plugin, extract_plugin=True):
                return app.response(message='插件更新成功')
            else:
                return app.response(code=500, message='插件安装失败')
        return app.response(code=500, message='插件下载失败')

    @app.route()
    async def uninstall_plugin(self, data: UninstallModel):
        bot.uninstall_plugin(data.plugin_id, remove=True)

        return app.response(message='插件卸载成功')
