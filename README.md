# Amiya-Bot

> 基于 [mirai-console](https://github.com/mamoe/mirai-console) 和 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的QQ聊天机器人<br>
> 其根本为一个 websocket 客户端，通过 TCP 接收到消息后，再以 HTTP 发送格式化的消息<br>

> 名字源于游戏 [《明日方舟》](https://ak.hypergryph.com/) 的女主角"阿米娅"，其主题与核心功能也和游戏相关。

    "博士，能再见到您……真是太好了。今后我们同行的路还很长，所以，请您多多关照！"

## 声明

- Amiya-Bot 是在《明日方舟》爱好者群体中诞生的以便捷功能为主的聊天机器人
- 本项目拒绝加入与金钱相关的功能，并在遵守法律法规且符合社会主义核心价值观的前提下使用
- 创建者需承诺不得使用本项目进行**任何形式的盈利行为**
- 本项目不承担因违反上述所带来的一切后果

## 已完成的功能

Amiya 的基础功能可以通过在QQ里向 Amiya 发送 `Amiya有什么功能` 来获得功能指引

- 信赖值与心情系统
- 查询干员精英化材料
- 查询干员专精材料
- 查询干员语音资料
- 查询敌方单位资料
- 查询材料怎么获得
- 公招查询（普通查询与图像识别）
- 模拟抽卡
- 合成玉计算
- 理智恢复提醒
- 查看明日方舟微博最新动态（自动推送与查询）

## 准备

- 想要创建自己的 Amiya，建议拥有一定编程基础，否则以下说明将难以理解
- <del>不了解编程的博士可以等待后续发布的`简易部署安装包`</del>
- 建议先去了解且能用任意方式成功运行 [mirai-console](https://github.com/mamoe/mirai-console)
  并加载插件 [mirai-api-http](https://github.com/project-mirai/mirai-api-http)
  ，关于 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的使用请到官方 Github 下查看
- 需要 python 3.7+
- 需要 Mysql 8.0+

## 注意

本项目代码含有以下特点

- 极少的注释
- 单线流程较为复杂
- 通过遍历文件的类加载方法
- 通过线程而非协程的异步实现方式

## 开始使用

1. 下载[资源文件](https://github.com/vivien8261/Amiya-Bot/releases/download/v3.0.1/amiya-bot-resource.zip)
2. 把字体文件放到目录`resource/style`下
3. 把表情包的图片放到目录`resource/images/face`下，支持 png 和 jpg 格式
4. 在 Mysql 里导入数据库文件`amiya.sql`
5. 配置`config.json`

```json5
{
  // 机器人QQ号
  "self_id": 1515361402,
  // 管理员QQ号
  "admin_id": 826197021,
  "server": {
    // mirai-api-http 服务配置
    "server_ip": "127.0.0.1",
    "server_port": 8060
  },
  "database": {
    // 数据库配置
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "amiya520",
    "db": "amiya"
  },
  "baidu_cloud": {
    // 百度智能云配置
    "enable": true,
    "app_id": "2152****",
    "api_key": "MM5pPVBBj***************",
    "secret_key": "XRfGzEZufj1MdNKyz***************"
  },
  "message": {
    // 文字消息的最大长度，超出则会转为图片发送
    "reply_text_max_length": 100
  },
  "close_beta": {
    // 是否启用封闭测试
    "enable": false,
    "group_id": 852191455
  }
}
```

6. 安装 python 依赖

```bash
pip install -r requirements.txt
```

7. 启动 `mirai-console` 并登录机器人QQ
8. 启动 Amiya 入口程序

```bash
python amiya.py
```

9. 短暂的启动过程后，若控制台显示了 websocket 连接成功，表示 Amiya 启动成功

```
...
websocket connecting success
```

10. 现在，唤醒你的 Amiya 吧！

## 功能使用注意

- **禁言会导致 Amiya 退群！！！**
- 要保证一些功能的使用，请导入资源文件中的`data.sql`（建议手动更新一次以保证使用最新的数据）
- 手动更新数据，最简单的方法，在根目录创建任意 python 脚本并运行以下代码

```python
from modules.updateGameData import UpdateGameData

if __name__ == '__main__':
    UGD = UpdateGameData()
    UGD.reset_all_data()
```

- 要使用抽卡功能，请在更新数据后，在数据表`t_pool`内维护卡池信息（`data.sql`带有初始的卡池数据）
- 自然语言处理方法和公招图像识别需要调用 [百度智能云](https://cloud.baidu.com/)
  的接口，如需使用需要自行申请并配置`config.json`

```json5
{
  "baidu_cloud": {
    // 是否启用百度智能云接口
    "enable": false,
    // APP ID
    "app_id": "",
    // API KEY
    "api_key": "",
    // SECRET KEY
    "secret_key": ""
  }
}
```

## 如何维护

- Amiya 带有`自动维护`功能，会在每天凌晨4点 <del>(鹰历)</del> 执行以下操作：
    - 清除图片缓存
    - 重置签到和心情值
    - 更新干员、公招和材料数据
    - 重启主程序
- 干员语音资料和敌人数据为即时从 wiki 获取，不需要维护
- 卡池目前需要手动到数据表`t_pool`维护，维护好的卡池可以通过 Amiya 切换卡池的功能进行更换
    - `Tips:` Pickup 的干员可以是虚构的不存在的干员，因为抽卡命中 Pickup 时，是直接使用 Pickup 字段的干员而非从干员表获取

```mysql
-- 新卡池数据插入语句示例
INSERT INTO t_pool (pool_name, pickup_6, pickup_5, pickup_4, limit_pool)
VALUES ('银灰色的荣耀',
        '银灰',
        '初雪,崖心',
        '角峰',
        0)
```

- 手动重启 Amiya 只需要重新运行`amiya.py`即可，不需要重启`mirai-console`。但建议每隔一段时间（2～3天）重启一次`mirai-console`以保证稳定

## 贡献

- 本项目欢迎 dalao 加入，拯救萌新，刻不容缓！
- 如果有更多的建议或 BUG 反馈，请提交到`issue`或官方测试群`362165038`
- 你的`star`将会成为 Amiya 成长的经验值

## TODO

- [ ] 修复语音
- [ ] 完善群事件
- [ ] 管理员命令功能
- [ ] WEB后台管理系统
- [ ] <del style="color: red">与明日方舟主题不相关的功能</del>

## 鸣谢

部分功能的信息需要从各大渠道获取，特鸣谢以下网站

- [明日方舟官方微博](https://m.weibo.cn/u/6279793937)
- [明日方舟工具箱](https://www.bigfun.cn/tools/aktools/)
- [PRTS - 玩家自由构筑的明日方舟中文Wiki](http://prts.wiki/) 