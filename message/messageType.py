import re

from modules.resource.imageManager import ImageManager
from modules.resource.voiceManager import VoiceManager
from library.imageCreator import create_image

imageManager = ImageManager()
voiceManager = VoiceManager()

voice_resource = 'resource/voices'


class Text:
    def __init__(self, text):
        chain = []

        r = re.findall(r'(\[face(\d+)])', text)
        if r:
            face = []
            for item in r:
                text = text.replace(item[0], ':face')
                face.append(item[1])

            for index, item in enumerate(text.split(':face')):
                if item != '':
                    chain.append({
                        'type': 'Plain',
                        'text': item
                    })
                if index <= len(face) - 1:
                    chain.append({
                        'type': 'Face',
                        'faceId': face[index]
                    })
        else:
            chain.append({
                'type': 'Plain',
                'text': text
            })

        self.item = chain


class Voice:
    def __init__(self, name, suffix='wav'):
        path = '%s/%s.%s' % (voice_resource, name, suffix)
        voice_id = voiceManager.voice(path, 'group')
        self.item = [
            {
                'type': 'Voice',
                'voiceId': voice_id
            }
        ]


class Image:
    def __init__(self, path):
        image_id = imageManager.image(path, 'group')
        self.item = [
            {
                'type': 'Image',
                'imageId': image_id
            }
        ]


class TextImage:
    def __init__(self, text, images=None):
        image = create_image(text, 'Common', images)
        image_id = imageManager.image('resource/message/Common/' + image, 'group')
        self.item = [
            {
                'type': 'Image',
                'imageId': image_id
            }
        ]
