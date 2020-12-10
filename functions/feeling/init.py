from database.baseController import BaseController
from message.messageType import MessageType
from modules.resource.voiceManager import VoiceManager
from modules.commonMethods import Reply

database = BaseController()
MSG = MessageType()
VM = VoiceManager()


class Init:
    def __init__(self):
        self.function_id = 'feeling'
        self.keyword = ['信赖', '关系', '好感']

    def action(self, data):
        result = database.user.get_user(data['user_id'])
        if result:
            feeling = result[1] if result[1] <= 4000 else 4000

            text = '阿米娅和博士的信赖值是 %d%s ~\n' % (int(feeling / 10), '%')
            if feeling >= 4000:
                text += '博士……我最近……是不是变得有点不像自己？那些偶然升起的无名怒火……是我的吗？就算这样，不，就算这样我也不会放弃。我会保护你的，博士，凭这把剑。'
                voice = '阿米娅(近卫)_信赖提升后交谈3'
            elif feeling >= 3000:
                text += '就算是现在，我也偶尔会想起米莎的眼神，想起霜星的怒吼，想起爱国者的嘶鸣……Ace、Scout以及许多干员为一个信念牺牲了自己。可大地上那么多的感染者，又是为了什么而死？'
                voice = '阿米娅(近卫)_信赖提升后交谈2'
            elif feeling >= 2400:
                text += '死亡应该铭刻在我们的记忆里，永不遗忘，无论这死亡是谁带来的，又是被带给了谁。我们的错误永远不会变成正确……那些疤痕应该要一直提醒我们，警告我们有多脆弱。'
                voice = '阿米娅(近卫)_信赖提升后交谈1'
            elif feeling >= 2000:
                text += '博士，我们的脚下，是一条漫长的道路……也许这是一次没有终点的旅行，但如果是和您一起，我觉得，非常幸福。'
                voice = '阿米娅_信赖提升后交谈3'
            elif feeling >= 1000:
                text += '嘿嘿，博士，悄悄告诉你一件事……我重新开始练小提琴了。是想在这次派对上给大家的惊喜，所以博士……要对大家保密哦'
                voice = '阿米娅_信赖提升后交谈2'
            elif feeling >= 400:
                text += '有时候，我会想起寒冷的家乡，那里就连空气中都弥漫着铜锈的味道。相比之下罗德岛是如此的温暖。所以，为了守护好这里，我必须更加努力才行。'
                voice = '阿米娅_信赖提升后交谈1'
            else:
                text += '博士，您工作辛苦了。'
                voice = '阿米娅_任命助理'

            # voice = VM.find_voice_id(voice)

            return Reply(text, auto_image=False)
            # return [Reply(text), Reply([MSG.voice(voice)], 0)]
        else:
            return Reply('博士还没有和阿米娅互动过呢～和阿米娅说【阿米娅会什么】来和阿米娅互动吧～')
