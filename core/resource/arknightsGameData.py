from abc import abstractmethod
from typing import List, Dict, Tuple, Any, Callable

STR_DICT = Dict[str, Any]
STR_DICT_MAP = Dict[str, STR_DICT]
STR_DICT_LIST = Dict[str, List[str]]
LIST_STR_DICT = List[STR_DICT]


class ArknightsGameData:
    version: str = ''
    enemies: Dict[str, Dict[str, dict]] = {}
    stages: STR_DICT_MAP = {}
    stages_map: STR_DICT_LIST = {}
    side_story_map: STR_DICT_MAP = {}
    operators: Dict[str, "Operator"] = {}
    tokens: Dict[str, "Token"] = {}
    birthday: Dict[str, Dict[str, List["Operator"]]] = {}
    materials: STR_DICT_MAP = {}
    materials_map: STR_DICT = {}
    materials_made: Dict[str, LIST_STR_DICT] = {}
    materials_source: STR_DICT_MAP = {}

    initialize_methods: List[Callable] = []

    @classmethod
    def initialize(cls):
        for method in cls.initialize_methods:
            method(cls)

    @staticmethod
    async def get_real_name(operator: str = None):
        ...


class ArknightsGameDataResource:
    @staticmethod
    async def get_skin_file(skin_data: dict, encode_url: bool = False):
        ...

    @staticmethod
    async def get_voice_file(operator: "Operator", voice_key: str, voice_type: str = ''):
        ...

    @staticmethod
    def parse_template(blackboard: list, description: str):
        ...


class ArknightsConfig:
    classes: Dict[str, str] = {}
    token_classes: Dict[str, str] = {}
    high_star: Dict[str, str] = {}
    types: Dict[str, str] = {}

    limit: List[str] = []
    unavailable: List[str] = []

    initialize_methods: List[Callable] = []

    @classmethod
    def initialize(cls):
        for method in cls.initialize_methods:
            method(cls)


class Operator:
    def __init__(self):
        self.data = {}

        self.id = ''
        self.cv = {}

        self.type = ''
        self.tags: List[str] = []
        self.range = ''
        self.rarity = 0
        self.number = ''

        self.name = ''
        self.en_name = ''
        self.wiki_name = ''
        self.index_name = ''
        self.origin_name = ''

        self.classes = ''
        self.classes_sub = ''
        self.classes_code = ''

        self.race = ''
        self.drawer = ''
        self.team_id = ''
        self.team = ''
        self.group_id = ''
        self.group = ''
        self.nation_id = ''
        self.nation = ''
        self.birthday = ''

        self.profile = ''
        self.impression = ''
        self.potential_item = ''

        self.limit = False
        self.unavailable = False
        self.is_recruit = False
        self.is_classic = False
        self.is_sp = False

    @abstractmethod
    def dict(self) -> STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def detail(self) -> Tuple[STR_DICT, STR_DICT]:
        raise NotImplementedError

    @abstractmethod
    def tokens(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def talents(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def potential(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def evolve_costs(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def skills(self) -> Tuple[LIST_STR_DICT, List[str], LIST_STR_DICT, Dict[str, LIST_STR_DICT]]:
        raise NotImplementedError

    @abstractmethod
    def building_skills(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def voices(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def stories(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def skins(self) -> LIST_STR_DICT:
        raise NotImplementedError

    @abstractmethod
    def modules(self) -> LIST_STR_DICT:
        raise NotImplementedError


class Token:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.en_name = ''
        self.description = ''
        self.classes = ''
        self.type = ''
        self.attr: LIST_STR_DICT = []
