class Resource:
    def __init__(self, db):
        self.db = db

    def add_image_id(self, image_name, image_type, mirai_id):
        cursor = self.db.cursor()

        sql = 'INSERT INTO t_images ( image_name, image_type, mirai_id ) VALUES ( "%s", "%s", "%s" )' \
              % (image_name, image_type, mirai_id)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def get_image_id(self, image_name, image_type):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_images WHERE image_name = "%s" AND image_type = "%s"' % (image_name, image_type)

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res

    def add_voice_id(self, voice_name, voice_type, mirai_id):
        cursor = self.db.cursor()

        sql = 'INSERT INTO t_voices ( voice_name, voice_type, mirai_id ) VALUES ( "%s", "%s", "%s" )' \
              % (voice_name, voice_type, mirai_id)

        self.db.ping(reconnect=True)
        cursor.execute(sql)

    def get_voice_id(self, voice_name, voice_type):
        cursor = self.db.cursor()

        sql = 'SELECT * FROM t_voices WHERE voice_name = "%s" AND voice_type = "%s"' % (voice_name, voice_type)

        self.db.ping(reconnect=True)
        cursor.execute(sql)
        res = cursor.fetchall()

        return res
