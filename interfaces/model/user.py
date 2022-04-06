from pydantic import BaseModel
from interfaces.model import SearchBase, Pagination


class UserTableSearch(SearchBase):
    black: str = None
    sign_in: str = None
    user_id: str = None


class UserTable(Pagination):
    search: UserTableSearch


class UserState(BaseModel):
    user_id: int
    black: int


class AddCoupon(BaseModel):
    users: list
    value: str

