from core.network import response
from core.network.httpServer.loader import interface
from core.network.httpServer.auth import AuthManager
from core.control import StateControl


class Bot:
    @staticmethod
    @interface.register()
    async def restart(auth=AuthManager.depends()):
        StateControl.shutdown()
        return response('准备重启...正在等待所有任务结束...')
