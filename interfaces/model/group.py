from typing import Union
from pydantic import BaseModel
from interfaces.model import SearchBase, Pagination


class GroupInfo(BaseModel):
    group_id: Union[int, str]


class GroupTableSearch(SearchBase):
    active: str = None
    group_id: str = None
    group_name: str = None
    permission: str = None
    send_notice: str = None
    send_weibo: str = None


class GroupTable(Pagination):
    search: GroupTableSearch


class GroupNoticeTableSearch(SearchBase):
    content: str = None
    send_user: str = None


class GroupNoticeTable(Pagination):
    search: GroupNoticeTableSearch


class GroupStatus(GroupInfo):
    active: int = None
    send_notice: int = None
    send_weibo: int = None


class Notice(BaseModel):
    notice_id: str = None
    content: str = None
