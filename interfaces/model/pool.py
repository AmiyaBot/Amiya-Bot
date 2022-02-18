from typing import List
from pydantic import BaseModel
from interfaces.model import SearchBase, Pagination


class PoolTableSearch(SearchBase):
    limit_pool: str = None
    pool_name: str = None


class PoolTable(Pagination):
    search: PoolTableSearch


class PoolSpItem(BaseModel):
    classes: str
    image: str
    operator_name: str
    rarity: str


class PoolInfo(BaseModel):
    pool_name: str
    pickup_4: str = None
    pickup_5: str = None
    pickup_6: str = None
    pickup_s: str = None
    limit_pool: str = None
    sp_list: List[PoolSpItem] = []


class GachaConfigItem(BaseModel):
    id: str
    operator_name: str
    operator_type: str


class GachaConfigSearch(SearchBase):
    operator_name: str = None
    operator_type: str = None


class GachaConfigTable(Pagination):
    search: GachaConfigSearch
