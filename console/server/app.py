import os
import sys
import datetime
import logging.config

from flask import Flask
from flask_cors import CORS
from gevent import pywsgi

from core import AmiyaBot
from core.util import log
from core.config import config

from .interface import Interface

logging.config.dictConfig({
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


class Console(Interface):
    def __init__(self, bot: AmiyaBot):
        conf = config.console
        path = self.app_path()
        app = Flask(__name__, static_folder=f'{path}/view/static', template_folder=f'{path}/view')

        app.secret_key = 'amiya_console'
        app.permanent_session_lifetime = datetime.timedelta(hours=3)

        CORS(app, supports_credentials=True)

        super().__init__(app, bot)

        host = (conf.host, conf.port)

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
        return os.path.dirname(__file__).replace('\\', '/').replace('console/server', '')
