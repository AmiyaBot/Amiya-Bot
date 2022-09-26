import sys
import jieba

if hasattr(sys, 'frozen'):
    jieba.set_dictionary('./dict.txt')

import srsly
import dhash
import server
import functions

from jieba import posseg
from core.lib import baiduCloud
