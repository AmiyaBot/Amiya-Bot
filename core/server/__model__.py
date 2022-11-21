from typing import Optional
from amiyabot.network.httpServer import BaseModel


class QueryData(BaseModel):
    currentPage: int = 1
    pageSize: int = 10
    search: Optional[str] = None
