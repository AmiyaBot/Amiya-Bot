import os
import yaml
import urllib.parse

from flask import Flask, request, make_response
from werkzeug.utils import secure_filename

from core import AmiyaBot
from core.util.common import make_folder
from dataSource import DataSource

from ..response import response

setting_path = 'configure/functionSetting.yaml'


def file_controller(app: Flask, bot: AmiyaBot, data: DataSource):
    @app.route('/getSourceDownloadState', methods=['POST'])
    def get_source_download_state():
        with open('resource/.src', mode='r') as file:
            content = file.read().strip('\n').split('\n')

        content = {item[0]: item[1] for item in [n.split('\t') for n in content]}

        return response(content)

    @app.route('/refreshSource', methods=['POST'])
    def refresh_source():
        data.download_bot_resource(refresh=True)
        data.get_ignore(reset=True)
        bot.restart()
        return response(message='即将进入重启，重启需要一定时间，请耐心等待...')

    @app.route('/getFunctionSetting', methods=['POST'])
    def get_function_setting():
        if os.path.exists(setting_path):
            with open(setting_path, mode='r') as f:
                return response(yaml.safe_load(f))
        return response(message='文件尚未创建')

    @app.route('/saveFunctionSetting', methods=['POST'])
    def save_function_setting():
        params = request.json
        with open(setting_path, mode='w+') as f:
            f.write(yaml.dump(params))
        return response(message='保存成功')

    @app.route('/upload', methods=['POST'])
    def upload():
        make_folder('resource/images/temp')

        file = request.files.get('file')
        filename = request.values.get('filename')
        if not filename:
            filename = secure_filename(file.filename)
        path = os.path.join('resource/images/temp', filename)
        file.save(path)

        return response(data={'filename': filename}, message='上传成功')

    @app.route('/images/<filename>', methods=['GET'])
    def images(filename):
        filename = urllib.parse.unquote(filename)
        path = f'resource/images/temp/{filename}'
        if os.path.exists(path):
            with open(path, mode='rb') as file:
                res = make_response(file.read())
            res.headers['Content-Type'] = 'image/jpg'
            return res
        else:
            return '资源不存在'
