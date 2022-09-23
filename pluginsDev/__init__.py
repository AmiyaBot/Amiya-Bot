import os
import sys
import copy
import shutil
import importlib

from contextlib import contextmanager


class ScriptModulesFinder:
    def __init__(self, *args: str):
        self.libs = args

    @contextmanager
    def __temp_sys_path(self, include: list = None):
        local_path = copy.deepcopy(sys.path)
        sys.path = [
            *[os.path.abspath(lib) for lib in self.libs],
            *(include or [])
        ]

        yield copy.deepcopy(local_path)

        sys.path = copy.deepcopy(local_path)

    def find(self, script: str, import_name: str, module_dir: str = None):
        module_dir = os.path.abspath(module_dir or os.path.dirname(script))

        if not os.path.exists(module_dir):
            os.makedirs(module_dir)

        with self.__temp_sys_path([module_dir, os.path.abspath(os.path.dirname(script))]) as local_path:
            not_exists = []

            done = False
            while not done:
                try:
                    module = importlib.import_module(import_name)
                except ModuleNotFoundError as e:
                    module_name = e.name
                    if module_name in not_exists:
                        raise e

                    for path in local_path:
                        target = os.path.join(path, module_name)
                        dest = os.path.join(module_dir, module_name)
                        if os.path.exists(target):
                            if os.path.isdir(target):
                                shutil.copytree(target, dest)
                            else:
                                shutil.copyfile(target, dest)
                        else:
                            if module_name not in not_exists:
                                not_exists.append(module_name)
                    continue

                done = True

        return module


finder = ScriptModulesFinder(
    'resource/env/python-standard-lib.zip',
    'resource/env/python-dlls',
    'resource/../'
)
