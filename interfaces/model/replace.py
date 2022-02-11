from pydantic import BaseModel
from interfaces.model import SearchBase, Pagination


class ReplaceItem(BaseModel):
    origin: str = None
    replace: str = None
    user_id: str = None
    group_id: str = None
    is_active: str = None
    is_global: str = None


class ReplaceDataItem(ReplaceItem):
    id: int
    in_time: int = None


class ReplaceTableSearch(SearchBase, ReplaceItem):
    pass


class ReplaceTable(Pagination):
    search: ReplaceTableSearch


class DeleteReplace(ReplaceDataItem):
    origin_all: bool = False
    replace_all: bool = False
    user_all: bool = False
    group_all: bool = False
    group_origin_all: bool = False


class ReplaceSettingItem(BaseModel):
    id: int = None
    text: str = None
    status: int = None
