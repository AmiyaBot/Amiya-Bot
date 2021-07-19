import os
import time
import threading

from database.baseController import BaseController
from library.imageCreator import clean_temp_images
from modules.commonMethods import maintain_record, insert_zero
from modules.network.httpRequests import HttpRequests

from functions.vblog.vblog import VBlog

database = BaseController()
blog = VBlog()


def run_automatic_action(websocket):
    threading.Thread(target=AutomaticAction(websocket).run_loop).start()


class AutomaticAction(HttpRequests):
    def __init__(self, websocket):
        super().__init__()

        self.websocket = websocket

    def run_loop(self):
        self.send_admin('启动完毕')
        while True:
            self.actions()
            time.sleep(30)

    def actions(self):
        threading.Timer(0, self.intellect_full_alarm).start()
        threading.Timer(1, self.send_new_blog).start()
        threading.Timer(2, self.maintain).start()

    def maintain(self):
        now = time.localtime(time.time())
        hour = now.tm_hour
        mint = now.tm_min
        try:
            if hour == 4 and mint == 0:
                record = maintain_record()
                now_time = int('%s%s%s' % (now.tm_year,
                                           insert_zero(now.tm_mon),
                                           insert_zero(now.tm_mday)))
                if record < now_time:
                    # 重置签到和心情值
                    database.user.reset_state()

                    # 清空消息及图片记录
                    database.message.del_message(days=7)
                    database.resource.del_image_id()

                    # 清除图片缓存
                    clean_temp_images()

                    # 记录维护时间
                    maintain_record(str(now_time))

                    self.send_admin('维护结束，最后维护时间 %s' % now_time)
        except Exception as e:
            self.send_admin('维护发生错误：' + str(e))

    def intellect_full_alarm(self):
        try:
            now = int(time.time())
            results = database.remind.check_intellect_full_alarm(now)
            if results:
                for item in results:
                    text = '博士！博士！您的理智已经满%d了，快点上线查看吧～' % item['full_num']
                    data = {
                        'user_id': item['user_id'],
                        'group_id': item['group_id'],
                        'type': item['message_type']
                    }
                    self.websocket.send_message(data, text, at=True)
        except Exception as e:
            self.send_admin('理智提醒发生错误：' + str(e))

    def send_new_blog(self):
        blog_file = 'temp/blog.txt'
        try:
            # 获取发送过的微博ID记录
            record_id = []
            if os.path.exists(blog_file):
                with open(blog_file, mode='r') as file:
                    record_id = file.read().split('\n')

            # 获取新ID
            new_id = blog.requests_content(only_id=True)

            if new_id and isinstance(new_id, str) and new_id not in record_id:
                new_blog = blog.requests_content()

                record_id.append(new_id)
                with open(blog_file, mode='w+') as file:
                    record_id = record_id[-5:] if len(record_id) >= 5 else record_id
                    file.write('\n'.join(record_id))

                group_list = self.get_group_list()
                time_record = time.time()
                total = 0

                self.send_admin('开始推送微博:\n%s' % new_id)

                disable_groups = database.function.get_disable_function_groups('vblog')

                for group in group_list:
                    if str(group['id']) in disable_groups:
                        continue
                    data = {'group_id': group['id'], 'type': 'group'}
                    for index, item in enumerate(new_blog):
                        if item.content:
                            self.websocket.send_message(data, message_chain=item.content, at=False)
                    total += 1

                complete = '微博推送完毕。已发送群 %d / %d，耗时：%ds' % \
                           (total, len(group_list), time.time() - time_record)

                self.send_admin(complete)
        except Exception as e:
            print('VBlog', e)
