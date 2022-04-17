import json
import time

from typing import Dict, Any
from core import bot, Message, Chain
from core.config import config
from core.network.httpRequests import http_requests
from core.util import read_yaml, is_all_chinese

covid_config = read_yaml('config/private/covid.yaml')

"""
reload_data_time: 上一次更新数据的时间戳
request_times_now: 从上次更新数据时起，共经过了多少次查询
reload_time: 数据有效时间
realod_request_times: 请求次数阈值
"""
reload_data_time = 0.0
request_times_now = 0
reload_time = covid_config.covidData.reloadTime
reload_request_times = covid_config.covidData.reloadRequestTimes

"""
covid_data: 疫情数据缓存
vaccine_top_data: 疫苗数据缓存
special: 特别行政区
"""
covid_data: Dict[str, Any] = dict()
vaccine_top_data: Dict[str, Any] = dict()
special = ['台湾', '香港', '澳门']


# 更新数据
async def get_data():
    global reload_data_time
    global request_times_now
    global covid_data
    global vaccine_top_data

    request_times_now += 1

    if time.time() - reload_data_time > reload_time or request_times_now >= reload_request_times:
        covid_data = json.loads(
            json.loads(await http_requests.get('https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5'))['data']
        )
        vaccine_top_data = json.loads(await http_requests.get('https://api.inews.qq.com/newsqa/v1/automation/modules'
                                                              '/list?modules=VaccineTopData'))['data']
        reload_data_time = time.time()
        request_times_now = 0


async def get_area_data(area_name: str):
    """
    获取行政区信息
    :param area_name: 行政区名
    :return: 候选行政区信息，形如["北京,朝阳", "辽宁,朝阳"]的列表
    """
    area = json.loads(await http_requests.get('https://apis.map.qq.com/ws/district/v1/search'
                                              '?&keyword=%s'
                                              '&key=%s' % (area_name, config.tencentLbs.key)))['result'][0]
    result = []
    for item in area:
        if item['level'] > 2:
            break
        result.append(item['address'])
    return result


# 获取中国疫苗信息
async def china_vaccine_trend():
    try:
        await get_data()
        data = vaccine_top_data['VaccineTopData']['中国']
        return data
    except KeyError:
        return None


# 获取世界疫苗信息
async def world_vaccine_trend():
    try:
        await get_data()
        data = vaccine_top_data['VaccineTopData']['全球']
        return data
    except KeyError:
        return None


async def city_covid(prov_name: str, city_name: str):
    """
    查询制定市级行政区疫情
    :param prov_name: 该市级行政区所在省级行政区名
    :param city_name: 该市级行政区名
    :return: 该地地址, 数据更新时间, 雷击确诊人数, 昨日新增确诊人数, 累计治愈, 累计死亡
    """
    try:
        await get_data()
        area_tree_data = covid_data['areaTree']
        for prov_data in area_tree_data[0]['children']:
            now_prov_name = prov_data['name']
            if prov_name != now_prov_name:
                continue
            for city_data in prov_data['children']:
                now_city_name = city_data['name']
                if now_city_name != city_name:
                    continue
                confirm = city_data['total']['confirm']
                confirm_add = city_data['today']['confirm']
                heal = city_data['total']['heal']
                dead = city_data['total']['dead']
                if prov_name in special:
                    prov_name = '中国' + prov_name
                return prov_name + city_name, covid_data['lastUpdateTime'], confirm, confirm_add, heal, dead
    except KeyError:
        if prov_name in special:
            prov_name = '中国' + prov_name
        return prov_name + city_name


async def prov_covid(prov_name: str):
    """
    查询制定省级行政区疫情
    :param prov_name: 该省级行政区名
    :return: 该地地址, 数据更新时间, 雷击确诊人数, 昨日新增确诊人数, 累计治愈, 累计死亡
    """
    try:
        await get_data()
        area_tree_data = covid_data['areaTree']
        for prov_data in area_tree_data[0]['children']:
            now_prov_name = prov_data['name']
            if now_prov_name != prov_name:
                continue
            confirm = prov_data['total']['confirm']
            confirm_add = prov_data['today']['confirm']
            heal = prov_data['total']['heal']
            dead = prov_data['total']['dead']
            if prov_name in special:
                prov_name = '中国' + prov_name
            return prov_name, covid_data['lastUpdateTime'], confirm, confirm_add, heal, dead
    except KeyError:
        if prov_name in special:
            prov_name = '中国' + prov_name
        return prov_name


async def china_covid():
    """
    查询中国疫情
    :return: '中国', 数据更新时间, 雷击确诊人数, 昨日新增确诊人数, 累计治愈, 累计死亡
    """
    try:
        await get_data()
        china_data = covid_data['areaTree'][0]
        confirm = china_data['total']['confirm']
        confirm_add = china_data['today']['confirm']
        heal = china_data['total']['heal']
        dead = china_data['total']['dead']
        return '中国', covid_data['lastUpdateTime'], confirm, confirm_add, heal, dead
    except KeyError:
        return '中国'


# async def *_query() 皆为疫情查询包装，用于提高代码可读性
async def pure_query():
    return await china_covid()


async def prov_or_city_query(data: Message):
    """
    单参数查询，在不确定该参数类型的情况下进行查询
    :param data: 消息
    :return: 该地区疫情数据
    """
    data_list = data.text.split(' ')
    # 如果配置中启用了位置服务，则进行模糊查询
    if config.tencentLbs.enable:
        # 获得该地区的信息
        result_list = await get_area_data(data_list[1])
        # 如果没有找到该地信息，则返回None
        if len(result_list) == 0:
            return None
        # 如果候选项有多个，则向用户询问
        index = 0
        if len(result_list) > 1:
            choose_text = ''
            for i in range(len(result_list)):
                choose_text += '\n' + str(i + 1) + '.' + result_list[i]
            index = int((await data.waiting(Chain(data).text('博士，阿米娅找到了以下相关地区，'
                                                             '发送序号来告诉阿米娅您想找的是哪一个吧！'
                                                             + choose_text))).text) - 1
        place = result_list[index].split(',')
        # 若该地区为省级行政区，则进行省级查询
        if len(place) == 1:
            return await prov_covid(place[0])
        # 否则进行市级查询
        return await city_covid(place[0], place[1])
    # 如果未启用位置服务，则该参数必然为省级行政区名，返回省级查询结果
    return prov_covid(data_list[1])


async def city_query(data: Message):
    data_list = data.text.split(' ')
    return await city_covid(data_list[1], data_list[2])


async def covid_query(data: Message):
    """
    疫情查询统一接口
    :param data: 消息
    :return: 查询函数，是否含有参数
    """
    func_dict = {
        1: pure_query,
        2: prov_or_city_query,
        3: city_query,
    }
    param_dict = {
        1: False,
        2: True,
        3: True,
    }
    return func_dict.get(len(data.text.split(' '))), param_dict.get(len(data.text.split(' ')))


# 疫情查询监听
@bot.on_group_message(keywords='疫情查询', level=10)
async def _(data: Message):
    data_list = data.text.split(' ')
    # 防止出现符号
    if not is_all_chinese(data_list):
        return Chain(data).text('博士，查询必须全中文哦！')
    # 获得查询接口等信息
    query = await covid_query(data)
    # 判断是否找到该地点
    if query is None:
        return Chain(data).text('博士，阿米娅没有找到该地点呢，可能是输入的地点格式不对哦！'
                                '格式应如下：\n兔兔疫情查询 <行政区名>（可选）')
    # 判断是否需要传参
    if query[1]:
        result = await query[0](data)
    else:
        result = await query[0]()
    # 判断是否查询到该地信息，若果len为1，则说明只返回了地名
    if len(result) == 1:
        return Chain(data).text('博士，未查询到 %s 疫情数据！请检查格式和是否有错别字后重试！（如多次出现此故障请联系开发者）' % result[0])
    # 返回查询结果
    return Chain(data).text('截止%s，%s 共有确诊病例%d例，昨日新增%d例，共治愈%d例，累计死亡%d例'
                            '\n数据来源：国家及各地卫健委每日信息发布'
                            '\n数据整合：腾讯新闻'
                            % (result[1], result[0], result[2], result[3],
                               result[4], result[5]))


# 全球疫苗查询借口
@bot.on_group_message(keywords='全球疫苗查询')
async def _(data: Message):
    return Chain(data).text('目前全球共报告接种新冠疫苗%d剂次'
                            '\n数据来源：OurWorldInData, WHO等官方数据'
                            '\n数据整合：腾讯新闻'
                            % (await world_vaccine_trend())['total_vaccinations'])


# 国内疫苗查询借口
@bot.on_group_message(keywords='国内疫苗查询')
async def _(data: Message):
    return Chain(data).text('目前国内共报告接种新冠疫苗%d剂次'
                            '\n数据来源：国家及各地卫健委每日信息发布'
                            '\n数据整合：腾讯新闻'
                            % (await china_vaccine_trend())['total_vaccinations'])


# 疫苗查询格式提示
@bot.on_group_message(keywords='疫苗查询')
async def _(data: Message):
    return Chain(data).text('博士，请使用“兔兔全球疫苗查询”或“兔兔国内疫苗查询”来查询疫苗信息哦！')
