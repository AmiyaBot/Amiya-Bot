import os
import sys

from logging.config import dictConfig
from gevent import pywsgi
from flask import Flask, render_template

from core.util.config import config
from core.util import log

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s][%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


class Console:
    def __init__(self):
        conf = config('console')
        path = self.app_path()
        app = Flask(__name__, static_folder=f'{path}/view/static', template_folder=f'{path}/view')

        @app.after_request
        def cors(environ):
            environ.headers['Access-Control-Allow-Origin'] = '*'
            environ.headers['Access-Control-Allow-Method'] = '*'
            environ.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
            return environ

        @app.route('/', methods=['GET'])
        def home():
            return render_template('index.html', input_text='', res_text='')

        host = (conf['host'], conf['port'])

        self.host = 'http://%s:%s' % host
        self.server = pywsgi.WSGIServer(host, app, log=app.logger)

    def start(self):
        log.info(f'console server running on {self.host}')
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass

    @staticmethod
    def app_path():
        if hasattr(sys, 'frozen'):
            return os.path.dirname(sys.executable)
        return '/'.join(sys.argv[0].replace('\\', '/').split('/')[0:-1])
