import collections
import json
import time
from typing import List

from core import bot, Message, Chain, log
from core.config import config
from core.network.httpRequests import http_requests

get_data_time = 0.0
reload_time = config.covidData.reloadTime
reload_request_times = config.covidData.reloadRequestTimes
request_time_now = 0

covid_data = collections.defaultdict
vaccine_top_data = collections.defaultdict
special = ['台湾', '香港', '澳门']


async def get_data():
    global get_data_time
    global request_time_now
    global covid_data
    global vaccine_top_data
    if time.time() - get_data_time > reload_time or request_time_now >= reload_request_times:
        covid_data = json.loads(
            json.loads(await http_requests.get('https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5'))['data']
        )
        vaccine_top_data = json.loads(await http_requests.get('https://api.inews.qq.com/newsqa/v1/automation/modules'
                                                              '/list?modules=VaccineTopData'))['data']
        get_data_time = time.time()
        request_time_now = 0
        log.info('Reload Covid Data')


def get_latest_correct_data(data: List[dict], key, err_val) -> dict:
    for i in range(1, len(data) + 1):
        if data[-i][key] != err_val:
            return data[-i]
    return None


async def china_vaccine_trend():
    try:
        await get_data()
        data = vaccine_top_data['VaccineTopData']['中国']
        return data
    except KeyError:
        return None


async def world_vaccine_trend():
    try:
        await get_data()
        data = vaccine_top_data['VaccineTopData']['全球']
        return data
    except KeyError:
        return None


async def city_covid(prov_name: str, city_name: str):
    try:
        await get_data()
        areaTree_data = covid_data['areaTree']
        for prov_data in areaTree_data[0]['children']:
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
    try:
        await get_data()
        areaTree_data = covid_data['areaTree']
        for prov_data in areaTree_data[0]['children']:
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


@bot.on_group_message(keywords='疫情查询')
async def _(data: Message):
    data_list = data.text.split(' ')
    if len(data_list) > 3:
        return Chain(data).text('博士，输入的地点格式不对哦！应遵循以下格式：'
                                '\n兔兔疫情查询 省级行政区名（可选） 市级行政区名（可选），'
                                '\n例如：'
                                '\n兔兔疫情查询'
                                '\n兔兔疫情查询 北京'
                                '\n兔兔疫情查询 北京 朝阳')
    if len(data_list) == 1:
        result = await china_covid()
    elif len(data_list) == 2:
        result = await prov_covid(data_list[1])
    else:
        result = await city_covid(data_list[1], data_list[2])
    place = ''
    if (len(data_list) == 1) or (len(data_list) > 1 and data_list[1] in special):
        place += '中国'
    place += ' '.join(data_list[1:])
    if result is None:
        return Chain(data).text('博士，未查询到 %s 疫情数据！原因可能是格式不符，应为：'
                                '\n兔兔疫情查询 省级行政区名（可选） 市级行政区名（可选），'
                                '\n例如：'
                                '\n兔兔疫情查询'
                                '\n兔兔疫情查询 北京'
                                '\n兔兔疫情查询 北京 朝阳' % place)
    return Chain(data).text('截止%s，%s 共有确诊病例%d例，昨日新增%d例，共治愈%d例，累计死亡%d例'
                            '\n数据来源：国家及各地卫健委每日信息发布'
                            '\n数据整合：腾讯'
                            % (result[0], place, result[1], result[2],
                               result[3], result[4]))


@bot.on_group_message(keywords='全球疫苗查询')
async def _(data: Message):
    return Chain(data).text('目前全球共接种了%d剂次新冠疫苗'
                            '\n数据来源：OurWorldInData, WHO等官方数据'
                            '\n数据整合：腾讯'
                            % (await world_vaccine_trend())['total_vaccinations'])


@bot.on_group_message(keywords='国内疫苗查询')
async def _(data: Message):
    return Chain(data).text('目前国内共接种了%d剂次新冠疫苗'
                            '\n数据来源：国家及各地卫健委每日信息发布'
                            '\n数据整合：腾讯'
                            % (await china_vaccine_trend())['total_vaccinations'])


@bot.on_group_message(keywords='疫苗查询')
async def _(data: Message):
    return Chain(data).text('博士，请使用“兔兔全球疫苗查询”或“兔兔国内疫苗查询”来查询疫苗信息哦！')
