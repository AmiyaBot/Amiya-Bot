import os
import time
import traceback

from core.util import log
from core.util.config import config
from core.util.common import insert_zero
from core.util.imageCreator import temp_dir
from core.database.models import User, Images, Message, Intellect


class AutomaticEvents:
    def __init__(self, bot):
        self.bot = bot

    def exec_all_tasks(self, times):
        self.maintain()
        self.intellect_full_alarm()

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
                    User.update(sign_in=0, user_mood=15).execute()

                    # 清空图片记录及一个月前的消息记录
                    last_time = int(time.time()) - 30 * 86400
                    Message.delete().where(Message.msg_time <= last_time).execute()
                    Images.truncate_table()

                    # 清除缓存
                    log.clean_log(3, extra=[temp_dir] + config('tempFolders'))

                    # 记录维护时间
                    maintain_record(str(now_time))

                    self.bot.send_to_admin(f'维护结束，最后维护时间{now_time}')
        except Exception as e:
            log.error(traceback.format_exc())
            self.bot.send_to_admin(f'维护发生错误：{repr(e)}')

    def intellect_full_alarm(self):
        try:
            conditions = (Intellect.status == 0, Intellect.full_time <= int(time.time()))
            results = Intellect.select().where(*conditions)
            if results:
                Intellect.update(status=1).where(*conditions).execute()
                for item in results:
                    item: Intellect
                    text = f'博士！博士！您的理智已经满{item.full_num}了，快点上线查看吧～'
                    self.bot.send_to_user(
                        message=text,
                        user_id=item.user_id,
                        group_id=item.group_id,
                        _type=item.message_type
                    )
        except Exception as e:
            log.error(traceback.format_exc())
            self.bot.send_to_admin(f'理智提醒发生错误：{repr(e)}')


def maintain_record(date: str = None):
    rc_path = 'log/maintainRecord.txt'

    if date:
        with open(rc_path, mode='w+') as rc:
            rc.write(date)
            return True

    if os.path.exists(rc_path):
        with open(rc_path, mode='r+') as rc:
            return int(rc.read())

    return 0
