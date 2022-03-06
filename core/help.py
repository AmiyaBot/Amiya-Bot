import os
import sys
import traceback

from typing import Any
from functools import wraps
from core.util import create_dir


class Helper:
    trace_files = {}

    @classmethod
    def record(cls, func) -> Any:
        @wraps(func)
        def decorated(*args, **kwargs):
            if not hasattr(sys, 'frozen'):
                trace = traceback.extract_stack()[-2]

                file = 'fileStorage/helpDocument.md'
                create_dir(file, is_file=True)

                filename = trace.filename.replace(os.getcwd(), '').strip('\\').replace('\\', '/')

                if filename not in cls.trace_files:
                    cls.trace_files[filename] = {}

                cls.trace_files[filename][trace.lineno] = trace.line

                content = '## Functions Indexes\n\n'
                for f, ls in cls.trace_files.items():
                    idx = '\n'.join(['- {ln:3} `{li}`'.format(ln=ln, li=li) for ln, li in ls.items()])
                    content += '### [%s](../%s)\n%s\n\n' % (f.replace('/__init__.py', ''), f, idx)

                with open(file, mode='w+', encoding='utf-8') as doc:
                    doc.write(content)

            return func(*args, **kwargs)

        return decorated
