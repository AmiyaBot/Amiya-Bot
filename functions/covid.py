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
    :return: 该地地址, 数据更新时间, 累计确诊人数, 昨日新增确诊人数, 累计治愈, 累计死亡
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
                return covid_data['lastUpdateTime'], confirm, confirm_add, heal, dead
    except KeyError:
        return None


async def prov_covid(prov_name: str):
    """
    查询制定省级行政区疫情
    :param prov_name: 该省级行政区名
    :return: 该地地址, 数据更新时间, 累计确诊人数, 昨日新增确诊人数, 累计治愈, 累计死亡
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
            return covid_data['lastUpdateTime'], confirm, confirm_add, heal, dead
    except KeyError:
        return None


async def china_covid():
    """
    查询中国疫情
    :return: '中国', 数据更新时间, 累计确诊人数, 昨日新增确诊人数, 累计治愈, 累计死亡
    """
    try:
        await get_data()
        china_data = covid_data['areaTree'][0]
        confirm = china_data['total']['confirm']
        confirm_add = china_data['today']['confirm']
        heal = china_data['total']['heal']
        dead = china_data['total']['dead']
        return covid_data['lastUpdateTime'], confirm, confirm_add, heal, dead
    except KeyError:
        return None


# 疫情查询监听
@bot.on_group_message(keywords='疫情查询')
async def _(data: Message):
    data_list = data.text.split(' ')
    # 防止出现符号
    if not is_all_chinese(data_list):
        return Chain(data).text('博士，地区名称必须为中文哦！')
    # 判断参数数量是否超限
    if len(data_list) > 3:
        return Chain(data).text('博士，输入地点的格式不对哦！')
    result = None
    # 如果没有参数，则返回中国疫情数据
    if len(data_list) == 1:
        result = await china_covid()
    # 如果有一个参数，则进行分类查询
    elif len(data_list) == 2:
        # 如果启用腾讯位置服务，则进行模糊查询
        if config.tencentLbs.enable:
            # 获取行政区信息
            result_list = await get_area_data(data_list[1])
            # 判断有没有该地信息
            if len(result_list) != 0:
                # 对多个候选项进行询问
                index = 0
                if len(result_list) > 1:
                    choose_text = ''
                    for i in range(len(result_list)):
                        choose_text += '\n' + str(i + 1) + '.' + result_list[i]
                    index = int((await data.waiting(Chain(data).text('博士，阿米娅找到了以下相关地区，发送序号来告诉阿米娅您想找的是哪一个吧！'
                                                                     + choose_text))).text) - 1
                place = result_list[index].split(',')
                # 根据对应等级进行分类
                if len(place) == 1:
                    result = await prov_covid(place[0])
                else:
                    result = await city_covid(place[0], place[1])
                    data_list[1] = place[0]
                    data_list.append(place[1])
        # 如果没有启用，则必然为省份查询，返回省份查询结果
        else:
            result = await prov_covid(data_list[1])
    # 如果有两个及以上参数，只返回市级数据
    else:
        result = await city_covid(data_list[1], data_list[2])
    place = ''
    # 对特别行政区进行特判
    if (len(data_list) == 1) or (len(data_list) > 1 and data_list[1] in special):
        place += '中国'
    place += ' '.join(data_list[1:])
    # 判空
    if result is None:
        return Chain(data).text('博士，未查询到【%s】疫情数据！请检查格式和是否有错别字后重试！（如多次出现此故障请联系开发者）' % place)
    # 返回数据
    return Chain(data).text('截至%s，【%s】共有确诊病例%d例，昨日新增%d例，共治愈%d例，累计死亡%d例'
                            '\n数据来源：国家及各地卫健委每日信息发布'
                            '\n数据整合：腾讯新闻'
                            % (result[0], place, result[1], result[2],
                               result[3], result[4]))


# 全球疫苗查询接口
@bot.on_group_message(keywords='全球疫苗查询')
async def _(data: Message):
    return Chain(data).text('目前全球共报告接种新冠病毒疫苗%d剂次'
                            '\n数据来源：OurWorldInData, WHO等官方数据'
                            '\n数据整合：腾讯新闻'
                            % (await world_vaccine_trend())['total_vaccinations'])


# 国内疫苗查询接口
@bot.on_group_message(keywords='疫苗查询')
async def _(data: Message):
    return Chain(data).text('目前国内共报告接种新冠病毒疫苗%d剂次'
                            '\n数据来源：国家及各地卫健委每日信息发布'
                            '\n数据整合：腾讯新闻'
                            % (await china_vaccine_trend())['total_vaccinations'])
