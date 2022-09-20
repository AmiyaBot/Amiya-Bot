import os
import sys
import json
import zipfile
import importlib

from amiyabot import PluginInstance

dist = 'plugins'

if __name__ == '__main__':
    if not os.path.exists(dist):
        os.makedirs(dist)

    profiles = []
    for root, dirs, _ in os.walk('./pluginsDev'):
        for item in dirs:
            plugin = os.path.join(root, item)

            if not os.path.exists(f'{plugin}/__init__.py') or '__pycache__' in plugin:
                continue

            print(f'packaging... {plugin}')

            path_split = plugin.replace('\\', '/').split('/')
            parent_dir = os.path.abspath('/'.join(path_split[:-1]))

            sys.path.append(parent_dir)
            sys.path.append(plugin)

            module = importlib.import_module(path_split[-1])

            instance: PluginInstance = getattr(module, 'bot')

            profiles.append({
                'name': instance.name,
                'version': instance.version,
                'plugin_id': instance.plugin_id,
                'plugin_type': instance.plugin_type,
                'description': instance.description
            })

            package = f'{dist}/{instance.plugin_id}-{instance.version}.zip'

            with zipfile.ZipFile(package, 'w') as pack:
                for plugin_root, _, files in os.walk(plugin):
                    for index, filename in enumerate(files):
                        target = os.path.join(plugin_root, filename)
                        if '__pycache__' in target:
                            continue
                        pack.write(target, target.replace(plugin + '\\', ''))

            sys.path.remove(parent_dir)
            sys.path.remove(plugin)

            print(f'\t --> {package}')

    with open(f'{dist}/plugins.json', mode='w', encoding='utf-8') as file:
        file.write(json.dumps(profiles, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': ')))
