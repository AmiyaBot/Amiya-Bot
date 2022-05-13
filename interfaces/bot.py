from core.network import response
from core.network.server.loader import interface
from core.network.server.auth import AuthManager
from core.control import StateControl


class Bot:
    @staticmethod
    @interface.register()
    async def restart(auth=AuthManager.depends()):
        StateControl.shutdown()
        return response('准备重启...正在等待所有任务结束...')
