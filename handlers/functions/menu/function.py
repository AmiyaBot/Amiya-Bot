class Function:
    source_code = 'https://github.com/vivien8261/Amiya-Bot'
    source_code_key = ['代码', '源码']
    query_key = ['可以做什么', '能做什么', '会做什么', '会干什么', '会什么', '有什么功能', '功能', '菜单']
    function_list = [
        {
            'id': 'normal',
            'title': '普通互动'
        },
        {
            'id': 'userInfo',
            'title': '查看个人信息'
        },
        {
            'id': 'replaceText',
            'title': '别名识别'
        },
        {
            'id': 'gacha',
            'title': '模拟抽卡'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员基础资料'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员精英化材料'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员技能专精材料'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员技能数据'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员模组信息'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员档案'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员语音资料'
        },
        {
            'id': 'checkOperator',
            'title': '查询干员立绘资料'
        },
        {
            'id': 'checkEnemy',
            'title': '查询敌方单位资料'
        },
        {
            'id': 'checkMaterial',
            'title': '查询材料或物品'
        },
        {
            'id': 'recruit',
            'title': '公招查询'
        },
        {
            'id': 'jadeCalculator',
            'title': '合成玉计算'
        },
        {
            'id': 'intellectAlarm',
            'title': '理智恢复提醒'
        },
        {
            'id': 'weibo',
            'title': '明日方舟微博'
        }
    ]
    function_titles = []
    function_groups = {}

    for item in function_list:
        function_titles.append(item['title'])
        if item['id']:
            if item['id'] not in function_groups:
                function_groups[item['id']] = []

            function_groups[item['id']].append(item['title'])
