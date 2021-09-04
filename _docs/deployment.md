# Amiya-Bot 4.0 开发者文档

## 环境要求
- [mirai-console](https://github.com/mamoe/mirai-console)
    - [mirai-api-http](https://github.com/project-mirai/mirai-api-http)
- [Python 3.7~3.8](https://www.python.org/)
mirai-console可使用mirai-console-loader代替。
> mirai-console-loader 是 mirai-console 的官方启动器，若能自己启动 mirai-console，可不使用。<br>
> 注意：**仅限 Windows 系统**。

## mirai 配置
此处略，详见[Amiya-Bot-resource的历史readme](https://github.com/vivien8261/Amiya-Bot-resource/blob/35726a7310c6beeffb9fde1dbf5415170e815d05/README.md)
注：除mirai配置部分(**不包括mirai-api-http**)外其他部分由于版本更新**已不具有参考价值**。
    mirai-api-http的使用请到[官方Github](https://github.com/project-mirai/mirai-api-http)下查看

## Amiya 配置
按照注释编辑`config.json`
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
        "authKey": "AMIYARESTART"
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
    // 是否启用离线测试
    "offline": false
}
```

## Python 配置

1.安装Python
略，或[此处](https://www.baidu.com/s?wd=python%E5%AE%89%E8%A3%85)

2. 安装依赖

```bash
pip install -r requirements.txt
```

Windows可直接运行requirements.cmd

## 启动

```bash
python amiya.py
```

或直接打开start.cmd（Windows）/start.sh（Linux）
注：Centos等自带Python2的系统应需使用python3命令。

```bash
python3 amiya.py
```

## 功能测试

- 离线测试
    - 不需要启动`mirai-console`
    - 配置 `offline: true` 直接运行脚本`quickStart.py`
    - 然后在控制台模拟交互

```bash
python quickStart.py
```

- 实际环境的封闭测试
    - 配置封闭测试相关项
    - 再通过上述步骤启动 Amiya
    - 之后，Amiya 仅会回应封闭测试指定的群

```json5
{
    "closeBeta": {
        "enable": true,
        "groupId": 653031149
    },
}
```
