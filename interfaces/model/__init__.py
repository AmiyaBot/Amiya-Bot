from pydantic import BaseModel


class SearchBase(BaseModel):
    orderByField: str = None
    orderBy: str = None


class Pagination(BaseModel):
    page: int = 1
    pageSize: int = 10
