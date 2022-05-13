from typing import Dict, Callable
from core.util import snake_case_to_pascal_case


class InterfaceLoader:
    @classmethod
    def register(cls,
                 router_path: str = None,
                 method: str = 'post',
                 **kwargs):
        def decorator(fn):
            def get_options():
                return fn, router_path, method, kwargs

            return get_options

        return decorator

    @classmethod
    def load_controller(cls, controller):
        attrs = [item for item in dir(controller) if not item.startswith('__')]
        methods: Dict[str, Callable] = {}

        for n in attrs:
            obj = getattr(controller, n)
            if hasattr(obj, '__call__'):
                methods[n] = obj

        cname = controller.__name__[0].lower() + controller.__name__[1:]

        for name, func in methods.items():
            fn, router_path, method, options = func()

            router_path = router_path or f'/{cname}/' + snake_case_to_pascal_case(name.strip('_'))

            yield fn, router_path, method, cname, options


interface = InterfaceLoader
