import abc
import json

from typing import List


class GeneralDefinition:
    @classmethod
    @abc.abstractmethod
    def builder(cls,
                command: str,
                sub_command: str = None,
                content: dict = None,
                options: dict = None):
        raise NotImplementedError('builder must be implemented when inheriting class GeneralDefinition.')

    @classmethod
    def friend_message(cls, session: str, target_id: int, chains: List[dict]):
        return cls.builder('sendFriendMessage', content={
            'sessionKey': session,
            'target': target_id,
            'messageChain': chains
        })

    @classmethod
    def group_message(cls, session: str, target_id: int, chains: List[dict], quote: int = None):
        return cls.builder('sendGroupMessage', options={'quote': quote}, content={
            'sessionKey': session,
            'target': target_id,
            'messageChain': chains
        })

    @classmethod
    def temp_message(cls, session: str, target_id: int, group_id: int, chains: List[dict]):
        return cls.builder('sendTempMessage', content={
            'sessionKey': session,
            'qq': target_id,
            'group': group_id,
            'messageChain': chains
        })

    @classmethod
    def mute(cls, session: str, target_id: int, member_id: int, time: int):
        return cls.builder('mute', content={
            'sessionKey': session,
            'target': target_id,
            'memberId': member_id,
            'time': time
        })

    @classmethod
    def nudge(cls, session: str, target_id: int, group_id: int):
        return cls.builder('sendNudge', content={
            'sessionKey': session,
            'target': target_id,
            'subject': group_id,
            'kind': 'Group'
        })


class WebsocketAdapter(GeneralDefinition):
    @classmethod
    def builder(cls,
                command: str,
                sub_command: str = None,
                content: dict = None,
                options: dict = None,
                sync_id: int = 1):
        return json.dumps(
            {
                'syncId': sync_id,
                'command': command,
                'subCommand': sub_command,
                'content': content,
                **(options or {})
            },
            ensure_ascii=False
        )


class HttpAdapter(GeneralDefinition):
    @classmethod
    def builder(cls,
                command: str,
                sub_command: str = None,
                content: dict = None,
                options: dict = None):
        return content
