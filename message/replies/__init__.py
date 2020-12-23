from .admin import admin
from .emotion import emotion
from .waiting import waiting
from .greeting import greeting
from .faceImage import faceImage


class Replies:
    def __init__(self):
        self.admin = admin
        self.emotion = emotion
        self.waiting = waiting
        self.greeting = greeting
        self.faceImage = faceImage
