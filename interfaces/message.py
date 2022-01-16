from pydantic import BaseModel
from core.network import response
from core.database.messages import MessageRecord, query_to_list


class GroupQuery(BaseModel):
    group_id: int


class Message:
    @classmethod
    async def get_message_by_group_id(cls, item: GroupQuery):
        return response(query_to_list(MessageRecord.select().where(MessageRecord.group_id == item.group_id)))
