import collections
import json
import math
import time
from enum import Enum
from json import JSONDecodeError

from typing import Dict, Any, List

from fake_useragent import UserAgent

from core import bot, Message, Chain, log
from core.config import config
from core.network.httpRequests import http_requests
from core.util import read_yaml, is_all_chinese, number_with_sign


class SyncStatus(Enum):
    success = 0
    syncing = 1
    unsync = 2
    failed = 3


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
covid_url: 疫情数据来源
sync_status: 同步数据状态，如果失败则停用该功能
covid_data: 疫情数据缓存
special: 特别行政区
input_key: 境外输入key
useless_key: 无效地区名key
min_eps: 最低bleu阈值
"""
covid_url = 'http://c.m.163.com/ug/api/wuhan/app/data/list-total'
sync_status = SyncStatus.unsync
covid_data: Dict[str, Any] = dict()
special = ['台湾', '香港', '澳门']
input_key = ['境外输入']
useless_key = ['未明确地区', '地区未确认', '待确认', '本土病例', '本土病例', '境外来沪', '外地来沪', '划归外省', '境外输入人员'] + input_key
min_eps = 0.6


# 更新数据
async def get_data():
    global reload_data_time
    global request_times_now
    global sync_status
    global covid_data

    if sync_status not in (SyncStatus.syncing, SyncStatus.failed) \
       and time.time() - reload_data_time > reload_time \
       or request_times_now >= reload_request_times:
        sync_status = SyncStatus.syncing
        try:
            data = json.loads(
                await http_requests.get(covid_url,
                                        headers={
                                            'user-agent': str(UserAgent().random)
                                        })
            )
            covid_data = None
            for country in data['data']['areaTree']:
                if country['name'] == '中国':
                    covid_data = country
                    break
        except JSONDecodeError:
            log.error(f'fail to sync covid data, maybe cause by the format of data from {covid_url}')
            sync_status = SyncStatus.failed
        else:
            sync_status = SyncStatus.success
            if covid_data is None:
                log.error(f'fail to sync covid data, maybe cause by the content of data from {covid_url}')
                sync_status = SyncStatus.failed
        finally:
            reload_data_time = time.time()
            request_times_now = 0


def bleu(cand: str, refer: str) -> float:
    if cand == refer:
        return 1.0
    n = min(len(cand), len(refer)) - 1
    cand_len = len(cand)
    refer_len = len(refer)
    score = 0.0
    for i in range(n):
        times = 0
        ref_dict = collections.defaultdict(int)
        for k in range(refer_len - i):
            w = ''.join(refer[k: k + i + 1])
            if ref_dict[w] is None:
                ref_dict[w] = 1
            else:
                ref_dict[w] += 1
        for k in range(cand_len - i):
            w = ''.join(cand[k: k + i + 1])
            if ref_dict.get(w) is not None and ref_dict[w] > 0:
                times += 1
                ref_dict[w] -= 1
        gram = times / (cand_len - i)
        if gram == 0:
            return 0.0
        score += math.log(gram)
    score /= n
    bp = math.exp(min(0, 1 - refer_len / cand_len))
    return math.exp(score) * bp


def search(area: str) -> List[str]:
    eps = max(min_eps, (len(area) - 2) / (len(area) - 1))
    search_result = []
    for prov in covid_data['children']:
        res = bleu(area, prov['name'])
        if res >= eps:
            search_result.append((prov['name'], res))
        for city in prov['children']:
            if city['name'] not in useless_key:
                res = bleu(area, city['name']) + bleu(area, prov['name'] + city['name'])
                res /= 2
                if res >= eps:
                    search_result.append((prov['name'] + ',' + city['name'], res))
    return [item[0] for item in sorted(search_result, key=lambda x: x[1], reverse=True)]


def find_data_by_addr(addr: str) -> dict:
    places = addr.split(',')
    if len(places) < 1:
        return covid_data
    for prov in covid_data['children']:
        if prov['name'] == places[0]:
            if len(places) == 1:
                return prov
            for city in prov['children']:
                if city['name'] == places[1]:
                    return city
    return None


def get_input(area: dict) -> tuple:
    for item in area['children']:
        if item['name'] in input_key:
            return item['total']['confirm'], item['today']['confirm']


# 疫情查询监听
@bot.on_group_message(keywords='疫情查询', level=3)
async def _(data: Message):
    if config.covid.enable and sync_status in (SyncStatus.unsync, SyncStatus.success):
        await get_data()
    data_list = data.text.split(' ')
    # 防止出现符号
    if not is_all_chinese(data_list):
        return Chain(data).text('博士，地区名称必须为中文哦！')
    # 判断是否为全国查询
    area_name = ''
    if len(data_list) == 1:
        query_covid_data = covid_data
        area_name = '中国'
        # 境外输入
        total_input = query_covid_data['total']['input']
        today_input = query_covid_data['today']['input']
        total_total_input_str = f'境外输入病例共{total_input}例，，' if total_input is not None else ''
        today_total_input_str = f'较昨日{number_with_sign(today_input)}例，' \
            if today_input is not None else ''
        input_str = total_total_input_str + today_total_input_str + '\n'
        # 无症状
        total_no_symptom = query_covid_data['extData']['noSymptom']
        today_no_symptom = query_covid_data['extData']['incrNoSymptom']
        total_no_symptom_str = f'无症状感染者共{total_no_symptom}例，' if total_no_symptom is not None else ''
        today_no_symptom_str = f'较昨日{number_with_sign(today_no_symptom)}例，' \
            if today_no_symptom is not None else ''
        symptom_str = total_no_symptom_str + today_no_symptom_str + '\n'
    else:
        data_list[1] = ''.join(data_list[1:])
        result = search(data_list[1])
        index = 0
        if len(result) == 0:
            return Chain(data).text(f'博士，未查询到 {area_name} 疫情数据！请检查格式和是否有错别字后重试！（如多次出现此故障请联系开发者）')
        if len(result) > 1:
            ask_str = '博士，阿米娅查询到了以下地点的疫情数据，发送序号来告诉阿米娅是哪一个吧！\n'
            for i in range(len(result)):
                ask_str += f'{i + 1}.{result[i]}\n'
            index = int((await data.waiting(Chain(data).text(ask_str))).text) - 1
            if not 0 <= index <= len(result) - 1:
                return Chain(data).text(f'博士，你没有输入序号哦！')
        result = result[index]
        place = result.split(',')
        query_covid_data = find_data_by_addr(result)
        # 对特别行政区进行特判
        if data_list[1] in special:
            area_name += '中国'
        area_name += ' '.join(place)
        # 判空
        if query_covid_data is None:
            return Chain(data).text(f'博士，未查询到 {area_name} 疫情数据！请检查格式和是否有错别字后重试！（如多次出现此故障请联系开发者）')
        # 境外输入
        input_result = get_input(query_covid_data)
        input_str = ''
        if input_result is not None:
            total_input, today_input = input_result
            input_str = f'境外输入共{total_input}，较昨日{number_with_sign(today_input)}例，\n'
        # 无症状
        symptom_str = ''
    # 数据更新时间
    lastUpdateTime = query_covid_data['lastUpdateTime']
    time_str = f'截至{lastUpdateTime}，' if lastUpdateTime is not None else ''
    # 确诊
    total_confirm = query_covid_data['total']['confirm']
    today_confirm = query_covid_data['today']['confirm']
    total_confirm_str = f'共有确诊病例{total_confirm}例，' if total_confirm is not None else ''
    today_confirm_str = f'较昨日{number_with_sign(today_confirm)}例，' if today_confirm is not None else ''
    comfirm_str = total_confirm_str + today_confirm_str + '\n'
    # 治愈
    total_heal = query_covid_data['total']['heal']
    today_heal = query_covid_data['today']['heal']
    total_heal_str = f'共治愈{total_heal}例，' if total_heal is not None else ''
    today_heal_str = f'较昨日{number_with_sign(total_heal)}例，' if today_heal is not None else ''
    heal_str = total_heal_str + today_heal_str + '\n'
    # 死亡
    total_dead = query_covid_data['total']['dead']
    today_dead = query_covid_data['today']['dead']
    total_dead_str = f'累计死亡{total_dead}例' if total_dead is not None else ''
    today_dead_str = f'，较昨日{number_with_sign(today_dead)}例。' if today_dead is not None else '。'
    dead_str = total_dead_str + today_dead_str + '\n'
    # 现有确诊
    total_store_confirm = total_confirm - total_heal - total_dead
    today_store_confirm = query_covid_data['today']['storeConfirm']
    total_store_confirm_str = f'现有病例共{total_store_confirm}例，' if total_store_confirm is not None else ''
    today_store_confirm_str = f'较昨日{number_with_sign(today_store_confirm)}例，' \
        if today_store_confirm is not None else ''
    store_confirm_str = total_store_confirm_str + today_store_confirm_str + '\n'
    return Chain(data).text_image(time_str + area_name + comfirm_str + '其中' + store_confirm_str + symptom_str
                                  + input_str + heal_str + dead_str + '\n数据来源：国家及各地卫健委每日信息发布'
                                  '\n数据整合：网易新闻')
