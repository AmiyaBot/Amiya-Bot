import os
import yaml
import time
import xlwt

from io import BytesIO
from werkzeug.utils import secure_filename
from flask import Flask, session, request, make_response
from core.util.common import make_folder, read_excel, time_string_to_stamp
from core.config import func_setting_path
from core.database.models import ReplaceText
from core.database.manager import model_to_dict, select_for_paginate, SearchParams

from ..response import response


def setting_controller(app: Flask):
    @app.route('/getFunctionSetting', methods=['POST'])
    def get_function_setting():
        if os.path.exists(func_setting_path):
            with open(func_setting_path, mode='r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return response(data)
        return response(message='文件尚未创建')

    @app.route('/saveFunctionSetting', methods=['POST'])
    def save_function_setting():
        params = request.json
        with open(func_setting_path, mode='w+', encoding='utf-8') as f:
            f.write(yaml.dump(params))
        return response(message='保存成功')

    @app.route('/setting/getReplaceTextByPages', methods=['POST'])
    def get_replace_text_by_pages():
        params = request.json
        search = SearchParams(
            params['search'],
            equal=['is_global', 'is_active'],
            contains=['user_id', 'group_id', 'origin', 'target']
        )

        data, count = select_for_paginate(ReplaceText,
                                          search,
                                          page=params['page'],
                                          page_size=params['pageSize'])

        return response({'count': count, 'data': data})

    @app.route('/setting/changeReplaceTextStatus', methods=['POST'])
    def change_replace_text_status():
        params = request.json
        replace_id = params['replace_id']

        ReplaceText \
            .update(is_global=params['is_global'], is_active=params['is_active']) \
            .where(ReplaceText.replace_id == replace_id) \
            .execute()

        return response(message='设置成功')

    @app.route('/setting/deleteReplaceText', methods=['POST'])
    def delete_replace_text():
        params = request.json
        replace_id = params['replace_id']

        if 'group_origin_all' in params:
            ReplaceText.delete().where(ReplaceText.group_id == params['group_id'],
                                       ReplaceText.origin == params['origin']).execute()
        elif 'user_all' in params:
            ReplaceText.delete().where(ReplaceText.group_id == params['group_id'],
                                       ReplaceText.user_id == params['user_id']).execute()
        elif 'group_all' in params:
            ReplaceText.delete().where(ReplaceText.group_id == params['group_id']).execute()
        elif 'all' in params:
            ReplaceText.delete().where(ReplaceText.origin == params['origin']).execute()
        else:
            ReplaceText.delete().where(ReplaceText.replace_id == replace_id).execute()

        return response(message='删除成功')

    @app.route('/setting/exportReplaceText', methods=['GET'])
    def export_replace_text():
        data = ReplaceText.select()
        book = xlwt.Workbook(encoding='utf-8')
        sheet = book.add_sheet('REPLACE')

        for col, field in enumerate(['ID', '提交用户', '用户所在群组', '原字符', '替换字符', '提交时间', '是否全局启用', '是否审核通过']):
            sheet.write(0, col, field)

        row = 1
        for item in data:
            for col, line in enumerate(model_to_dict(item).items()):
                field = line[0]
                value = line[1]

                if field == 'in_time':
                    value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))

                sheet.write(row, col, value)
            row += 1

        sio = BytesIO()
        book.save(sio)
        sio.seek(0)

        res = make_response(sio.getvalue())
        res.headers['Content-type'] = 'application/vnd.ms-excel'
        res.headers['Content-Disposition'] = 'attachment;filename=data.xlsx'

        return res

    @app.route('/setting/importReplaceText', methods=['POST'])
    def import_replace_text():
        make_folder('resource/files')

        file = request.files.get('file')
        filename = request.values.get('filename')
        if not filename:
            filename = secure_filename(file.filename)
        path = os.path.join('resource/files', filename)
        file.save(path)

        excel = read_excel(path)
        data = []

        for row in excel[0][1:]:
            data.append({
                'user_id': row[1] or int(session.get('user')),
                'group_id': row[2] or int(session.get('user')),
                'origin': row[3],
                'target': row[4],
                'in_time': time_string_to_stamp(row[5]) or int(time.time()),
                'is_global': int(row[6].split('.')[0]),
                'is_active': int(row[7].split('.')[0])
            })

        print(data)

        ReplaceText.delete().execute()
        ReplaceText.insert_many(data).execute()

        return response(data={'filename': filename}, message='导入成功')
