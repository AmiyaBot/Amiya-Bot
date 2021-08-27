import os
import random


def get_face(name: str = None):
    face_dir = 'resource/images/face/'
    images = []
    for root, dirs, files in os.walk(face_dir.strip('/')):
        for item in files:
            if item != '.gitkeep':
                if name == item:
                    return face_dir + item
                images.append(face_dir + item)

    return random.choice(images)
