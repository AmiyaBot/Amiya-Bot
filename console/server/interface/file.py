import os
import urllib.parse

from flask import Flask, request, make_response
from werkzeug.utils import secure_filename

from core.util.common import make_folder

from ..response import response


def file_controller(app: Flask):
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
