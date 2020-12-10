# Amiya-Bot

> 基于 [mirai-console](https://github.com/mamoe/mirai-console) 和 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的QQ聊天机器人<br>
> 其根本为一个 websocket 客户端，通过 TCP 接收到消息后，再以 HTTP 发送格式化的消息<br>

> 名字源于游戏《明日方舟》的女主角"阿米娅"，其主题与核心功能也和游戏相关。

    "博士，能再见到您……真是太好了。今后我们同行的路还很长，所以，请您多多关照！"

## 声明

- Amiya-Bot 是在《明日方舟》爱好者群体中诞生的以便捷功能为主的聊天机器人，本项目拒绝加入与金钱相关的功能，并在遵守法律法规且符合社会主义核心价值观的前提下使用。<br>
- 创建者需承诺不得使用本项目进行`任何形式的盈利行为`<br>
- 本项目不承担因违反上述所带来的一切后果

## 准备

- 想要创建自己的 Amiya，建议拥有一定编程基础，否则以下说明将难以理解
- 建议先去了解且能用任意方式成功运行 [mirai-console](https://github.com/mamoe/mirai-console)
  并加载插件 [mirai-api-http](https://github.com/project-mirai/mirai-api-http)
  ，关于 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的使用请到官方 Github 下查看
- 需要 python 3.7+
- 需要 Mysql 8.0+

## 注意

本项目代码含有以下特点

- 极少的注释
- 代码关系复杂
- 较为新手的编码手法
- 莫名其妙的异步方式
- 不讲道理的类加载方法

## 开始使用

1. 下载资源文件
2. 把字体文件放到目录`resource/style`下
3. 把表情包的图片放到目录`resource/images/face`下，支持png和jpg格式
4. 在 Mysql 里导入数据库文件 `amiya.sql`
5. 配置 `config.json`

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
  "natural_language": {
    // 自然语言处理配置
    "enable": true,
    "app_id": "2152****",
    "api_key": "MM5pPVBBj***************",
    "secret_key": "XRfGzEZufj1MdNKyz***************"
  },
  "message": {
    // 文字消息的最大长度，超出则会转为图片发送
    "reply_text_max_length": 100
  }
}
```

6. 安装 python 依赖

```commandline
pip install -r requirements.txt
```

7. 启动 `mirai-console` 并登录机器人QQ
8. 启动 Amiya

```commandline
python amiya.py
```

9. 在QQ里和Amiya说 `Amiya会什么` 开始使用吧

## 功能使用注意

- 要使用查询类功能，请于启动Amiya前，获取一次材料及干员数据。最简单的方法，在根目录创建 `update.py` 并运行以下代码

```python
from modules.updateGameData import UpdateGameData

if __name__ == '__main__':
    UGD = UpdateGameData()
    UGD.reset_all_data()
```

- 要使用抽卡功能，请在获取干员数据后，在数据表`t_pool`内维护卡池信息，也可以导入资源文件`t_pool.sql`
- 自然语言处理方法需要调用 [百度智能云](https://cloud.baidu.com/)
  的接口，如需使用需要自行申请并配置`config.json`

```json5
{
  "natural_language": {
    // 是否启用自然语言处理
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

## 贡献

- 本项目欢迎dalao加入，拯救萌新，刻不容缓！
- 如果有更多的建议或BUG反馈，请提交到`issue`或官方测试群`362165038`
- 你的`star`将会成为Amiya成长的经验值

## TODO

- [ ] 修复语音
- [ ] 管理员功能
- [ ] 完善群事件
- [ ] 不知道哪天会突发奇想的奇怪功能
- [ ] <del>与明日方舟主题不相关的功能</del>
- [ ] 一键式安装包，适合不了解编程的博士在没有环境的电脑下运行

## 鸣谢

部分功能的信息需要从各大渠道获取，特鸣谢以下网站

- [明日方舟官方微博](https://m.weibo.cn/u/6279793937)
- [明日方舟工具箱](https://www.bigfun.cn/tools/aktools/)
- [PRTS - 玩家自由构筑的明日方舟中文Wiki](http://prts.wiki/) 