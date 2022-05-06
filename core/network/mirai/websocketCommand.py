import json
from abc import ABCMeta, abstractmethod
from typing import List

from core.network.mirai import func_with_name
from core.util import Singleton


class WebsocketCommandClass(metaclass=Singleton):
    class PluginInfoClass(metaclass=Singleton):
        @func_with_name(name='About')
        def About(self, syncId: int = 1):
            return build_command(command='about', syncId=syncId)

    class MessageCacheClass(metaclass=Singleton):
        @func_with_name(name='MessageFromId')
        def MessageFromId(self, sessionKey: str, id: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'id': id
            }, command='messageFromId', syncId=syncId)

    class AccountInfoClass(metaclass=Singleton):
        @func_with_name(name='FriendList')
        def FriendList(self, sessionKey: str, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey
            }, command='friendList', syncId=syncId)

        @func_with_name(name='GroupList')
        def GroupList(self, sessionKey: str, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey
            }, command='groupList', syncId=syncId)

        @func_with_name(name='MemberList')
        def MemberList(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='memberList', syncId=syncId)

        @func_with_name(name='BotProfile')
        def BotProfile(self, sessionKey: str, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey
            }, command='botProfile', syncId=syncId)

        @func_with_name(name='FriendProfile')
        def FriendProfile(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='friendProfile', syncId=syncId)

        @func_with_name(name='MemberProfile')
        def MemberProfile(self, sessionKey: str, target: int, memberId: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'memberId': memberId
            }, command='memberProfile', syncId=syncId)

        @func_with_name(name='UserProfile')
        def UserProfile(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
            }, command='userProfile', syncId=syncId)

    class MessageSendClass(metaclass=Singleton):
        @func_with_name(name='SendFriendMessage')
        def SendFriendMessage(self, sessionKey: str, target: int,
                              messageChain: List[dict], syncId: int = 1, **kwargs):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'messageChain': messageChain
            }, command='sendFriendMessage', syncId=syncId, **kwargs)

        @func_with_name(name='SendGroupMessage')
        def SendGroupMessage(self, sessionKey: str, target: int,
                             messageChain: List[dict], syncId: int = 1, **kwargs):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'messageChain': messageChain
            }, command='sendGroupMessage', syncId=syncId, **kwargs)

        @func_with_name(name='SendTempMessage')
        def SendTempMessage(self, sessionKey: str, group: int, qq: int,
                            messageChain: List[dict], syncId: int = 1, **kwargs):
            return build_command(content={
                'sessionKey': sessionKey,
                'qq': qq,
                'group': group,
                'messageChain': messageChain
            }, command='sendTempMessage', syncId=syncId, **kwargs)

        @func_with_name(name='SendNudge')
        def SendNudge(self, sessionKey: str, target: int,
                      subject: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'subject': subject
            }, command='sendNudge', syncId=syncId)

    class MessageRecallClass(metaclass=Singleton):
        @func_with_name(name='RecallMessage')
        def RecallMessage(self, sessionKey: str, messageId: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'messageId': messageId
            }, command='recall', syncId=syncId)

    class FileOperateClass(metaclass=ABCMeta):
        @abstractmethod
        def FileList(*args, **kwargs):
            raise NotImplementedError('FileList is not implemented.')

        @abstractmethod
        def FileInfo(*args, **kwargs):
            raise NotImplementedError('FileInfo is not implemented.')

        @abstractmethod
        def FileDelete(*args, **kwargs):
            raise NotImplementedError('FileDelete is not implemented.')

        @abstractmethod
        def FileMove(*args, **kwargs):
            raise NotImplementedError('FileMove is not implemented.')

        @abstractmethod
        def FileRename(*args, **kwargs):
            raise NotImplementedError('FileRename is not implemented.')

        @abstractmethod
        def DirectoryMake(*args, **kwargs):
            raise NotImplementedError('DirectoryMake is not implemented.')

    class AccountManageClass(metaclass=Singleton):
        @func_with_name(name='DeleteFriend')
        def DeleteFriend(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='deleteFriend', syncId=syncId)

    class AdminOperateClass(metaclass=Singleton):
        @func_with_name(name='Mute')
        def Mute(self, sessionKey: str, target: int, memberId: int, time: int = 0, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'memberId': memberId,
                'time': time
            }, command='mute', syncId=syncId)

        @func_with_name(name='UnMute')
        def UnMute(self, sessionKey: str, target: int, memberId: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'memberId': memberId,
            }, command='unmute', syncId=syncId)

        @func_with_name(name='Kick')
        def Kick(self, sessionKey: str, target: int, memberId: int, msg: str, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'memberId': memberId,
                'msg': msg
            }, command='kick', syncId=syncId)

        @func_with_name(name='Quit')
        def Quit(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='quit', syncId=syncId)

        @func_with_name(name='MuteAll')
        def MuteAll(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='muteAll', syncId=syncId)

        @func_with_name(name='UnMuteAll')
        def UnMuteAll(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='unmuteAll', syncId=syncId)

        @func_with_name(name='SetEssence')
        def SetEssence(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='setEssence', syncId=syncId)

        @func_with_name(name='GroupConfigGet')
        def GroupConfigGet(self, sessionKey: str, target: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target
            }, command='groupConfig', subcommand='get', syncId=syncId)

        @func_with_name(name='GroupConfigUpdate')
        def GroupConfigUpdate(self, sessionKey: str, target: int, config: dict, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'config': config
            }, command='groupConfig', subcommand='update', syncId=syncId)

        @func_with_name(name='MemberInfoGet')
        def MemberInfoGet(self, sessionKey: str, target: int, memberId: int, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'memberId': memberId
            }, command='memberInfo', subcommand='get', syncId=syncId)

        @func_with_name(name='MemberInfoUpdate')
        def MemberInfoUpdate(self, sessionKey: str, target: int, memberId: int, info: dict, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'memberId': memberId,
                'info': info
            }, command='memberInfo', subcommand='update', syncId=syncId)

        @func_with_name(name='')
        def MemberAdmin(self, sessionKey: str, target: int, memberId: int, assign: bool, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'target': target,
                'memberId': memberId,
                'assgin': assign
            }, command='memberAdmin', syncId=syncId)

    class GroupAnnounceClass(metaclass=Singleton):
        @func_with_name(name='AnnoList')
        def AnnoList(self, id: int, offset: int, size: int, syncId: int = 1):
            return build_command(content={
                'id': id,
                'offset': offset,
                'size': size
            }, command='anno_list', syncId=syncId)

        @func_with_name(name='AnnoPublish')
        def AnnoPublish(self, target: int, content: str, pinned: bool = False, syncId: int = 1, **kwargs):
            return build_command(content={
                'target': target,
                'content': content,
                'pinned': pinned,
            }, command='anno_publish', syncId=syncId, **kwargs)

        @func_with_name(name='AnnoDelete')
        def AnnoDelete(self, id: int, fid: int, syncId: int = 1):
            return build_command(content={
                'id': id,
                'fid': fid
            }, command='anno_delete', syncId=syncId)

    class EventHandleClass(metaclass=Singleton):
        @func_with_name(name='NewFriendRequestEvent')
        def NewFriendRequestEvent(self, sessionKey: str, eventId: int, fromId: int, groupId: int,
                                  operate: int, msg: str, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'eventId': eventId,
                'fromId': fromId,
                'groupId': groupId,
                'operate': operate,
                'message': msg
            }, command='resp_newFriendRequestEvent', syncId=syncId)

        @func_with_name(name='MemberJoinRequestEvent')
        def MemberJoinRequestEvent(self, sessionKey: str, eventId: int, fromId: int, groupId: int,
                                   operate: int, msg: str, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'eventId': eventId,
                'fromId': fromId,
                'groupId': groupId,
                'operate': operate,
                'message': msg
            }, command='resp_memberJoinRequestEvent', syncId=syncId)

        @func_with_name(name='BotInvitedJoinGroupRequestEvent')
        def BotInvitedJoinGroupRequestEvent(self, sessionKey: str, eventId: int, fromId: int, groupId: int,
                                            operate: int, msg: str, syncId: int = 1):
            return build_command(content={
                'sessionKey': sessionKey,
                'eventId': eventId,
                'fromId': fromId,
                'groupId': groupId,
                'operate': operate,
                'message': msg
            }, command='resp_botInvitedJoinGroupRequestEvent', syncId=syncId)

    def __init__(self):
        self.PluginInfo = self.PluginInfoClass()
        self.MessageCache = self.MessageCacheClass()
        self.AccountInfo = self.AccountInfoClass()
        self.MessageSend = self.MessageSendClass()
        self.MessageRecall = self.MessageRecallClass()
        self.AccountManage = self.AccountManageClass()
        self.AdminOperate = self.AdminOperateClass()
        self.GroupAnnounce = self.GroupAnnounceClass()
        self.EventHandle = self.EventHandleClass()

    @classmethod
    def build_command(cls, command, subcommand=None, content=None, syncId: int = 1, **kwargs):
        if content:
            return cls.__build_command__(content={
                **content,
                **kwargs
            }, command=command, subcommand=subcommand, syncId=syncId)
        return cls.__build_command__(content={
            **kwargs
        }, command=command, subcommand=subcommand, syncId=syncId)

    @classmethod
    def __build_command__(cls, command, subcommand=None, syncId: int = 1, **kwargs):
        return json.dumps({
                **{
                    'syncId': syncId,
                    'command': command,
                    'subCommand': subcommand
                }, **kwargs
            },
            ensure_ascii=False
        )


build_command = WebsocketCommandClass.build_command

WebsocketCommand = WebsocketCommandClass()
