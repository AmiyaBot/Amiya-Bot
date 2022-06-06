from enum import Enum


class Status(Enum):
    DEAD = -1
    UNMODIFIED = -1
    UNSYNCED = -1
    SYNCING = 0
    ALIVE = 1
    MODIFIED = 1
    SYNCED = 1


dispatch_events: dict = {}
tasks: set = set()
