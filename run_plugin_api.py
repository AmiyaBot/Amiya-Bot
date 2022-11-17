import os
import time
import shutil
import base64
import logging
import hashlib
import asyncio

from fastapi import File, UploadFile
from amiyabot import AmiyaBot
from amiyabot.util import create_dir, random_code, argv
from amiyabot.network.httpServer import HttpServer, BaseModel
from amiyabot.database import ModelClass, MysqlConfig, CharField, TextField, table, connect_database, query_to_list

from amiya import load_resource
from build.uploadFile import COSUploader

HOST = argv('host') or '0.0.0.0'
PORT = argv('port', int) or 8020
SECRET_ID = argv('secret-id')
SECRET_KEY = argv('secret-key')
MYSQL_HOST = argv('mysql-host') or '127.0.0.1'
MYSQL_PORT = argv('mysql-port', int) or 3306
MYSQL_USER = argv('mysql-user') or 'root'
MYSQL_PWD = argv('mysql-password')
SSL_KEY = argv('ssl-keyfile')
SSL_CERT = argv('ssl-certfile')

server = HttpServer(HOST, PORT, uvicorn_options={
    'ssl_keyfile': SSL_KEY,
    'ssl_certfile': SSL_CERT
})
uploader = COSUploader(SECRET_ID, SECRET_KEY,
                       logger_level=logging.FATAL)


@table
class Plugins(ModelClass):
    file: str = CharField(unique=True)
    name: str = CharField(null=True)
    version: str = CharField(null=True)
    plugin_id: str = CharField(null=True)
    plugin_type: str = CharField(null=True)
    description: str = CharField(null=True)
    logo: str = TextField(null=True)
    author: str = CharField(null=True)
    secret_key: str = CharField(null=True)
    upload_time: str = CharField(null=True)

    class Meta:
        database = connect_database('custom_plugins', True, MysqlConfig(MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PWD))


class CommitModel(BaseModel):
    file: str
    name: str
    version: str
    plugin_id: str
    plugin_type: str
    description: str
    logo: str
    author: str
    secret_key: str


@server.app.post('/uploadPlugin')
async def upload(file: UploadFile = File(...)):
    dest = f'uploads/dest/{int(time.time())}{random_code(10)}'
    path = f'uploads/plugins/{file.filename}'

    create_dir(dest)
    create_dir(path, is_file=True)

    with open(path, mode='wb') as f:
        f.write(await file.read())

    plugin = AmiyaBot.load_plugin(path, extract_plugin=True, extract_plugin_dest=dest)

    logo = ''
    if plugin.path:
        logo_path = os.path.join(dest, 'logo.png')
        if os.path.exists(logo_path):
            with open(logo_path, mode='rb') as ico:
                logo = 'data:image/png;base64,' + base64.b64encode(ico.read()).decode()

    shutil.rmtree(dest)
    data = {
        'file': file.filename,
        'name': plugin.name,
        'version': plugin.version,
        'plugin_id': plugin.plugin_id,
        'plugin_type': plugin.plugin_type,
        'description': plugin.description,
        'logo': logo,
        'warning': [],
        'error': [],
        'ready': True
    }

    exists: Plugins = Plugins.get_or_none(plugin_id=plugin.plugin_id)
    if exists:
        data['warning'].append(f'插件【{plugin.plugin_id}】已存在，你需要验证插件密钥。')
        if exists.version != plugin.version:
            data['warning'].append(f'版本变更：{plugin.version} >> {exists.version}')
        if exists.name != plugin.name:
            data['warning'].append('插件名称更新')
        if exists.description != plugin.description:
            data['warning'].append('插件描述更新')

    if plugin.plugin_type == 'official':
        data['error'].append('不允许上传标签为【官方】的插件，请修改 plugin_type 属性。')
        data['ready'] = False

    return data


@server.app.post('/commitPlugin')
async def commit(data: CommitModel):
    if not data.secret_key:
        return server.response(message='密钥不能为空', code=500)

    md5 = hashlib.md5((data.plugin_id + data.secret_key).encode())
    key = md5.hexdigest()

    exists: Plugins = Plugins.get_or_none(plugin_id=data.plugin_id)
    if exists and exists.secret_key != key:
        return server.response(message='密钥不匹配', code=500)

    path = os.path.abspath(f'uploads/plugins/{data.file}')
    uploader.upload_file(path, f'plugins/custom/{data.file}')

    Plugins.delete().where(Plugins.file == data.file).execute()
    Plugins.create(**{
        **data.dict(),
        'secret_key': key,
        'upload_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    })

    return server.response(message='提交成功')


@server.app.post('/deletePlugin')
async def delete(data: CommitModel):
    if not data.secret_key:
        return server.response(message='密钥不能为空', code=500)

    md5 = hashlib.md5((data.plugin_id + data.secret_key).encode())
    key = md5.hexdigest()

    exists: Plugins = Plugins.get_or_none(plugin_id=data.plugin_id)
    if exists and exists.secret_key != key:
        return server.response(message='密钥不匹配', code=500)

    Plugins.delete().where(Plugins.file == data.file).execute()

    return server.response(message='下架成功')


@server.app.post('/getPlugins')
async def get():
    return server.response(
        data=query_to_list(Plugins.select())
    )


load_resource()
asyncio.run(server.serve())
