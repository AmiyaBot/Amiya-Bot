import os
import sys
import srsly
import dhash
import requests_html

from . import server
from jieba import posseg
from core.lib import baiduCloud
from core.database import bot
from core.database import group
from core.database import messages
from core.database import user

from amiyabot.builtin.lib.imageCreator import FontStyle
from amiyabot.builtin.messageChain import ChainConfig

if hasattr(sys, 'frozen'):
    DIR_PATH = os.path.dirname(os.path.realpath(sys.executable))

    FontStyle.file = os.path.join(DIR_PATH, '_assets/font/HarmonyOS_Sans_SC.ttf')
    ChainConfig.md_template = os.path.join(DIR_PATH, '_assets/markdown/template.html')
    ChainConfig.md_template_dark = os.path.join(DIR_PATH, '_assets/markdown/template-dark.html')
