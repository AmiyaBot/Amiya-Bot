from .greeting import greeting
from .emotion import emotion
from .waiting import waiting
from .faceImage import faceImage


class Replies:
    def __init__(self):
        self.greeting = greeting
        self.emotion = emotion
        self.waiting = waiting
        self.faceImage = faceImage
