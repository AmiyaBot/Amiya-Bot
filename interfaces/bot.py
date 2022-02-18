from core.network import response
from core.network.httpServer.auth import AuthManager
from core.control import StateControl


class Bot:
    @classmethod
    async def restart(cls, auth=AuthManager.depends()):
        StateControl.shutdown()
        return response('准备重启...正在等待所有任务结束...')
