from flask import Flask, render_template

from core import AmiyaBot

from .auth import auth_controller
from .file import file_controller
from .user import user_controller
from .admin import admin_controller
from .gacha import gacha_controller
from .group import group_controller
from .operator import operator_controller
from .dashboard import dashboard_controller


class Intreface:
    def __init__(self, app: Flask, bot: AmiyaBot):
        @app.route('/', methods=['GET'])
        def home():
            return render_template(['index.html'], input_text='', res_text='')

        data = bot.handlers.arknights

        auth_controller(app, bot)
        file_controller(app)
        user_controller(app)
        admin_controller(app)
        gacha_controller(app)
        group_controller(app, bot)
        operator_controller(app, data)
        dashboard_controller(app)
