from core.network import response
from core.network.httpServer.auth import AuthManager
from core.database.messages import MessageRecord, query_to_list

from interfaces.model.group import GroupInfo


class Message:
    @classmethod
    async def get_message_by_group_id(cls, item: GroupInfo, auth=AuthManager.depends()):
        return response(
            query_to_list(
                MessageRecord.select().where(MessageRecord.group_id == item.group_id)
            )
        )
