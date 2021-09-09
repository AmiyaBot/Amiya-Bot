# Amiya-Bot 4.0 开发者文档

## 关于 Amiya-Bot 3.0 迁移到 4.0

- 4.0 版本重写了大部分核心代码并舍弃了 Mysql 数据库，已导致 3.0 的代码无法迁移。
- 4.0 在启动时会在目录下创建 `amiya.db` Sqlite 数据库。内含的 `user` 表与旧版本 `t_user` 表字段一致。用户数据可以手动迁移到Sqlite

## 代码部署

> 简单三步，启动你的 Amiya

1. 安装 python 依赖

```bash
pip install -r requirements.txt
```

2. 配置`config.json`

```json5
{
    // 机器人 QQ 号
    "selfId": 1515361402,
    // 管理员 QQ 号
    "adminId": 826197021,
    "server": {
        // mirai-api-http 服务配置
        "serverIp": "127.0.0.1",
        "httpPort": 8080,
        "websocketPort": 8060,
        "authKey": "AmiyaBot"
    },
    "console": {
        // console 管理员后台配置
        "host": "0.0.0.0",
        "port": 8000
    },
    "baiduCloud": {
        // 百度智能云配置
        "enable": false,
        "appId": "",
        "apiKey": "",
        "secretKey": ""
    },
    "message": {
        // 消息指令的频率限制
        "limit": {
            "seconds": 10,
            "maxCount": 3
        },
        // 文字回复的最大字符长度，超出则会转为图片发送
        "replyMaxLength": 100
    },
    "closeBeta": {
        // 是否启用封闭测试
        "enable": false,
        "groupId": 653031149
    },
    "tempFolders": [],
    "miraiFolder": "",
    // 是否启用离线测试
    "offline": false
}
```

3. 启动 Amiya 入口程序

```bash
python amiya.py
```

## 功能测试方式

- 离线测试
    - 不需要启动 `mirai-console`
    - 配置 `offline: true` 直接运行脚本 `quickStart.py`
    - 然后在控制台模拟交互

```bash
python quickStart.py
```

- 实际环境的封闭测试
    - 配置封闭测试相关项后启动 Amiya
    - 之后，Amiya 仅会回应封闭测试指定的群

```json5
{
    "closeBeta": {
        "enable": true,
        "groupId": 653031149
    },
    "offline": false
}
```
