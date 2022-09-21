import os

from core import app, bot


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

            res.append({
                'name': item.name,
                'version': item.version,
                'plugin_id': item.plugin_id,
                'plugin_type': item.plugin_type,
                'description': item.description,
                'document': content
            })

        return app.response(res)
