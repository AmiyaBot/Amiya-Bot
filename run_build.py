# -*- coding: UTF-8 -*-

import sys


def argv(name, formatter=str):
    key = f'--{name}'
    if key in sys.argv:
        index = sys.argv.index(key) + 1

        if index >= len(sys.argv):
            return True

        if sys.argv[index].startswith('--'):
            return True
        else:
            return formatter(sys.argv[index])


if __name__ == '__main__':
    build_type = argv('type')

    if build_type == 'package':
        from build.package import build

        build(
            argv('version'),
            argv('folder') or 'package',
            argv('branch'),
            argv('force'),
            argv('upload')
        )
    elif build_type == 'plugins':
        from pluginDev.buildPlugins import build

        build(argv('folder') or 'plugins', argv('upload'))
