import abc

from typing import Union


class WSOperation:
    @abc.abstractmethod
    async def connect_websocket(self):
        """
        建立连接
        :return:
        """
        pass

    @abc.abstractmethod
    async def send_message(self, reply):
        """
        发送消息的方式，传入 Chain 对象
        :param reply: Chain 对象
        :return:
        """
        pass

    @abc.abstractmethod
    async def send_command(self, command: str):
        """
        发送命令
        :param command: 命令内容
        :return:
        """
        pass

    @abc.abstractmethod
    async def handle_message(self, message: str):
        """
        处理消息
        :param message:
        :return:
        """
        pass

    @abc.abstractmethod
    async def handle_error(self, message: str):
        """
        处理异常
        :param message:
        :return:
        """
        pass


def response(data: Union[str, int, float, bool, dict, list] = None,
             code: int = 200,
             message: str = ''):
    """
    HTTP 请求的响应体

    :param data:    响应的数据
    :param code:    响应码
    :param message: 响应消息
    :return:
    """
    return {
        'data': data,
        'code': code,
        'message': message
    }
