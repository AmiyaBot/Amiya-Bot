from typing import Union
from attrdict import AttrDict


class Remote:
    cos: str
    wiki: str


class ResourceConfig:
    remote: Remote


resource_config: Union[ResourceConfig, AttrDict] = AttrDict({
    'remote': {
        'cos': 'https://cos.amiyabot.com',
        'wiki': 'https://static.prts.wiki'
    }
})
