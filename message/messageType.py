class MessageType:
    def __init__(self):
        pass

    @staticmethod
    def at(user_id):
        return {
            'type': 'At',
            'target': user_id
        }

    @staticmethod
    def at_all():
        return {
            'type': 'AtAll',
            'target': 0
        }

    @staticmethod
    def text(text):
        return {
            'type': 'Plain',
            'text': text
        }

    @staticmethod
    def face(face_id):
        return {
            'type': 'Face',
            'faceId': face_id
        }

    @staticmethod
    def image(image_id):
        return {
            'type': 'Image',
            'imageId': image_id
        }

    @staticmethod
    def voice(voice_id):
        return {
            'type': 'Voice',
            'voiceId': voice_id
        }

    def chain(self, data):
        chain = []
        for item in data:
            if 'at' in item:
                chain.append(self.at(item['at']))
            if 'text' in item:
                chain.append(self.text(item['text']))
            if 'image' in item:
                chain.append(self.image(item['image']))
            if 'face' in item:
                chain.append(self.face(item['face']))
        return chain
