import os
import shutil
import base64
import asyncio

from fastapi import File, UploadFile
from amiyabot import AmiyaBot
from amiyabot.util import create_dir
from amiyabot.network.httpServer import HttpServer

from amiya import load_resource

server = HttpServer('0.0.0.0', 8001)


@server.app.post('/upload_plugin')
async def upload(file: UploadFile = File(...)):
    path = f'uploads/plugins/{file.filename}'

    create_dir(path, is_file=True)

    with open(path, mode='wb') as f:
        f.write(await file.read())

    check_bot = AmiyaBot('', '')
    check_bot.install_plugin(path, extract_plugin=True)

    pid = list(check_bot.plugins.keys())[0]
    item = check_bot.plugins[pid]

    logo = ''
    if item.path:
        item_path = item.path[-1]
        logo_path = os.path.join(item_path, 'logo.png')
        if os.path.exists(logo_path):
            with open(logo_path, mode='rb') as ico:
                logo = 'data:image/png;base64,' + base64.b64encode(ico.read()).decode()

    data = {
        'file': file.filename,
        'name': item.name,
        'version': item.version,
        'plugin_id': item.plugin_id,
        'plugin_type': item.plugin_type,
        'description': item.description,
        'logo': logo
    }

    shutil.rmtree(item.path[-1])

    return data


load_resource()
asyncio.run(server.serve())
