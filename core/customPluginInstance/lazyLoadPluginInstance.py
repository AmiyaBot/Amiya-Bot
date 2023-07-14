from amiyabot import PluginInstance


class LazyLoadPluginInstance(PluginInstance):
    def __init__(self,
                 name: str,
                 version: str,
                 plugin_id: str,
                 plugin_type: str = None,
                 description: str = None,
                 document: str = None,
                 priority: int = 1):
        super().__init__(
            name,
            version,
            plugin_id,
            plugin_type,
            description,
            document,
            priority
        )

    def load(self): ...
