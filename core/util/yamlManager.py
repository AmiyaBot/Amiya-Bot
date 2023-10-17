import os
import yaml

from yaml import SafeDumper
from attrdict import AttrDict

from .common import create_dir


class YamlManager:
    yaml_cache = {'attr': {}, 'dict': {}}

    @classmethod
    def read_yaml(cls, path: str, _dict: bool = False, _refresh=True):
        t = 'dict' if _dict else 'attr'

        if path in cls.yaml_cache[t] and not _refresh:
            return cls.yaml_cache[t][path]

        with open(path, mode='r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            if not _dict:
                content = AttrDict(content)

            cls.yaml_cache[t][path] = content

        return content

    @classmethod
    def create_yaml(cls, path: str, data: dict, overwrite: bool = False):
        SafeDumper.add_representer(
            type(None),
            lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:null', ''),
        )
        create_dir(path, is_file=True)

        if os.path.exists(path) and not overwrite:
            return False

        with open(path, mode='w+', encoding='utf-8') as file:
            yaml.safe_dump(data, file, indent=4, default_flow_style=False, allow_unicode=True)

        return True
