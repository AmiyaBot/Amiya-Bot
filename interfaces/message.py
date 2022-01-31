from core.network import response
from core.network.httpServer.auth import AuthManager
from core.database.messages import MessageRecord, query_to_list

from interfaces.model.group import GroupInfo


class Message:
    @classmethod
    async def get_message_by_group_id(cls, items: GroupInfo, auth=AuthManager.depends()):
        message = query_to_list(
            sorted(
                MessageRecord.select().where(MessageRecord.group_id == items.group_id),
                key=lambda n: n.create_time
            )
        )

        return response(message)
