class Databases:
    message: str
    group: str
    user: str
    bot: str

    @classmethod
    def desc(cls):
        return {
            'message': 'database/message.db',
            'group': 'database/group.db',
            'user': 'database/user.db',
            'bot': 'database/bot.db',
        }
