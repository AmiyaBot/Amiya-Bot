import json


def response(data=None, message=None, code=200):
    return json.dumps(
        {
            'code': code,
            'data': data,
            'message': message
        },
        ensure_ascii=False
    )
