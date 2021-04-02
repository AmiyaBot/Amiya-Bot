import re

from message.messageType import TextImage
from modules.commonMethods import Reply

source_code = 'https://github.com/vivien8261/Amiya-Bot'
source_code_key = ['代码', '源码']


class Init:
    def __init__(self):
        self.function_id = 'functionQuery'
        self.keyword = ['可以做什么', '能做什么', '会做什么', '会干什么', '会什么', '有什么功能', '功能', '菜单'] + source_code_key

    @staticmethod
    def action(data):

        message = data['text_digits']

        function_list = [
            {
                'title': '群管理员功能',
                'desc': [
                    '【群管理员功能仅限群主与群管理员使用】',
                    '发送「阿米娅休息」在本群关闭阿米娅',
                    '发送「阿米娅工作」在本群开启阿米娅'
                ]
            },
            {
                'title': '查看个人信息',
                'desc': ['发送比如「阿米娅查看我的信息」']
            },
            {
                'title': '查询干员精英化材料',
                'desc': ['发送比如「阿米娅查看阿米娅精二材料」']
            },
            {
                'title': '查询干员技能专精材料',
                'desc': [
                    '发送比如「阿米娅查看阿米娅专三材料」',
                    '发送比如「阿米娅查看奇美拉专三材料」',
                    '发送比如「阿米娅查看阿米娅三技能专三材料」'
                ]
            },
            {
                'title': '查询干员技能数据',
                'desc': [
                    '发送比如「阿米娅查看阿米娅7级技能」',
                    '发送比如「阿米娅查看奇美拉7级」',
                    '发送比如「阿米娅查看阿米娅三技能专三」'
                ]
            },
            {
                'title': '查询干员档案',
                'desc': [
                    '发送比如「阿米娅查看阿米娅基础档案」',
                    '目前可查询的档案如下',
                    '【基础档案】',
                    '【综合性能检测结果】',
                    '【客观履历】',
                    '【档案资料一】',
                    '【综合体检测试】',
                    '【临床诊断分析】',
                    '【档案资料二】',
                    '【档案资料三】',
                    '【档案资料四】',
                    '【源石技艺评定】',
                    '【晋升记录】',
                    '【晋升资料】',
                    '【升变档案一】'
                ]
            },
            {
                'title': '查询干员语音资料',
                'desc': [
                    '发送比如「阿米娅查看阿米娅晋升2语音」'
                ]
            },
            {
                'title': '查询敌方单位资料',
                'desc': [
                    '发送比如「阿米娅查看敌人塔露拉」'
                ]
            },
            {
                'title': '查询材料怎么获得',
                'desc': ['发送比如「阿米娅固源岩怎么获得」']
            },
            {
                'title': '公招查询',
                'desc': [
                    '发送比如「阿米娅公招生存防护」',
                    '发送「阿米娅公招」后，发送公招的游戏截图，可以自动识别Tags查询'
                ]
            },
            {
                'title': '模拟抽卡',
                'desc': [
                    '发送「阿米娅 N 连抽」或「阿米娅抽卡 N 次」',
                    '发送「阿米娅卡池列表」可以查看卡池列表',
                    '发送「阿米娅卡池切换 "卡池名称" 」可以切换卡池',
                    '发送比如「阿米娅剩余多少抽卡券」可以查看抽卡券余额'
                ]
            },
            {
                'title': '合成玉计算',
                'desc': ['发送比如「阿米娅2020年8月15日前可得到多少玉」（年份非必须）']
            },
            {
                'title': '理智恢复提醒',
                'desc': [
                    '发送「阿米娅理智 N 满 N 告诉我」',
                    '记录提醒后发送「阿米娅理智回复了多少」查看进度'
                ]
            },
            {
                'title': '查看明日方舟微博最新动态',
                'desc': [
                    '发送比如「阿米娅最新动态」',
                    '【被动】当微博动态更新时阿米娅会主动推送新微博到群'
                ]
            },
            {
                'title': '查看阿米娅的源代码',
                'desc': 'source_code'
            }
        ]

        for item in source_code_key:
            if item in message:
                return Reply(source_code)

        for item in ['第(\\d+)(.*)功能', '功能(\\d+)']:
            r = re.search(re.compile(item), message)
            if r:
                index = int(r.group(1))
                if 0 < index <= len(function_list):
                    index -= 1
                    text = '【%s】' % function_list[index]['title']

                    if function_list[index]['desc'] == 'source_code':
                        return Reply(source_code)

                    for sub_item in function_list[index]['desc']:
                        text += '\n%s' % sub_item

                    return Reply(TextImage(text))

        text = '博士，这是阿米娅的功能清单，请发送「阿米娅查看第 N 个功能」来获取使用方法吧\n'
        for index, item in enumerate(function_list):
            text += '\n[%d] %s' % (index + 1, item['title'])

        return Reply(TextImage(text))
