from dataclasses import dataclass


@dataclass
class Friend:
    id: int
    nickname: str
    remark: str


@dataclass
class Group:
    id: int
    name: str
    permission: str


@dataclass
class Subject:
    id: int
    kind: str


@dataclass
class Client:
    id: int
    platform: str


class GroupMember:
    def __init__(self, data):
        self.id = data['id']
        self.memberName = data['memberName']
        self.specialTitle = data['specialTitle']
        self.permission = data['permission']
        self.joinTimestamp = data['joinTimestamp']
        self.lastSpeakTimestamp = data['lastSpeakTimestamp']
        self.muteTimeRemaining = data['muteTimeRemaining']
        self.group = Group(**data['group'])
