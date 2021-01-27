import os
import importlib

from database.baseController import BaseController
from modules.commonMethods import word_in_sentence

database = BaseController()
priority = [
    'functionQuery',
    'feeling',
    'gacha',
    'material',
    'operator',
    'recruit',
    'enemy',
    'jadeCalculator',
    'intellect',
    'vblog'
]


class FunctionsIndex:
    def __init__(self):
        index = len(priority)
        functions = {}
        for root, dirs, files in os.walk('functions'):
            for name in dirs:
                path = os.path.join(root, name)
                if '__pycache__' not in path:
                    module_path = '%s.init' % path.replace('\\', '/').replace('/', '.')
                    module = importlib.import_module(module_path, package='functions')
                    if name in priority:
                        functions[priority.index(name)] = module.Init()
                    else:
                        functions[index] = module.Init()
                        index += 1

        self.functions = []
        for key in sorted(functions):
            self.functions.append(functions[key])

    def action(self, data):
        for index, item in enumerate(self.functions):
            if word_in_sentence(data['text'], item.keyword):
                result = item.action(data)
                if result:
                    database.function.add_function_use_num(item.function_id)
                    return result
