from database.sqlCombiner import Mysql, Formula, Where


class Resource:
    def __init__(self, db: Mysql):
        self.db = db

    def add_image_id(self, image_name, image_type, mirai_id):
        self.db.insert('t_images', data={
            'image_name': image_name,
            'image_type': image_type,
            'mirai_id': mirai_id
        })

    def get_image_id(self, image_name, image_type):
        return self.db.select('t_images', where=Where({
            'image_name': image_name,
            'image_type': image_type
        }), fetchone=True)

    def add_voice_id(self, voice_name, voice_type, mirai_id):
        self.db.insert('t_voices', data={
            'voice_name': voice_name,
            'voice_type': voice_type,
            'mirai_id': mirai_id
        })

    def get_voice_id(self, voice_name, voice_type):
        return self.db.select('t_voices', where=Where({
            'voice_name': voice_name,
            'voice_type': voice_type
        }), fetchone=True)

    def del_image_id(self):
        self.db.truncate('t_images')
