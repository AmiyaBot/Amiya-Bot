# Amiya-Bot 4.0 开发者文档

## 关于 Amiya-Bot 3.0 迁移到 4.0

- 4.0 版本重写了大部分核心代码并舍弃了 Mysql 数据库，已导致 3.0 的代码无法迁移。
- 4.0 在启动时会在目录下创建 `amiya.db` Sqlite 数据库。内含的 `user` 表与旧版本 `t_user` 表字段一致。用户数据可以手动迁移到Sqlite

## 代码部署

> 简单三步，启动你的 Amiya

1. 安装 python 依赖

```bash
pip3 install -r requirements.txt
```

> 依赖中的 graiax-silkcoder 库，若在 Windows 下安装，可能会出现编译失败的问题。原因是该库需要操作系统特定编译环境<br>
> 安装 `Visual Studio 生成工具` 可解决此问题。<br>
> > 友情帮助，你可以选择以下任意方式安装：<br>
> > 1. 通过 Microsoft 官网的 Visual Studio 安装程序安装 `Visual Studio 生成工具`<br>
> > 2. 下载离线镜像文件安装：<br>
       [百度网盘](https://pan.baidu.com/s/1zf2Zl8NRTW22eKJYFIfyvA) ，提取码 `tdbp` <br>
       [阿里网盘](https://www.aliyundrive.com/s/1S13Tcvf1bp)

2. 配置`config.yaml`

```yaml
# 账号设置
account:
    # bot 账号
    bot: 1515361402
    # 管理员账号
    admin: 826197021
    # 主群设置
    group:
        # 主群群号
        groupId: 362165038
        # 封闭测试开关
        closeBeta: false

# mirai-api-http 配置
miraiApi:
    # IP 地址
    host: 127.0.0.1
    # 端口
    port:
        # http 服务端口
        http: 8080
        # websocket 服务端口
        ws: 8060
    # authkey
    authKey: AmiyaBot
    # mirai-console 的根目录路径，可为空，用于通过 path 参数发送静态文件。不配置的情况下，默认通过上传的方式发送
    folder:

# Amiya-Bot console IP 和端口配置
console:
    host: 0.0.0.0
    port: 80

# 百度智能云配置
baiduCloud:
    enable: false
    appId:
    apiKey:
    secretKey:

# 消息设置
message:
    # 消息限制
    limit:
        seconds: 10
        maxCount: 3
    # 文字自动转化为图片的长度
    transToImageLength: 100

# 常规设置
setting:
    # 离线模式
    offline: false
```

3. 启动 Amiya 入口程序

```bash
python amiya.py
```

> 在 Linux 下，最好使用<br>
> ```bash
> python3 amiya.py
> ```
> 或使用启动脚本（不同系统可能有些许不同，建议查阅 [此处](https://www.baidu.com/) ）<br>
> ```bash
> ./start.sh
> ```
> Windows 系统可使用启动脚本 `start.cmd` 启动（也可使用控制台手动启动）<br>
> 注：Windows 启动脚本**需要管理员权限**，将会自动删除另一系统的启动脚本，更改 NTP 服务器至 `ntp.ntsc.ac.cn` （中国科学院国家授时中心）并校时（仅 Windows），且会在每次启动前更换 `pypi` 镜像至 `华为云` 并执行依赖检查。

## 功能测试方式

- 离线测试
    - 离线测试不需要启动 `mirai-console`
    - 配置 `offline: true` 直接运行脚本 `quickTest.py`
    - 可在脚本内选择测试方式。注意，测试方式只能使用一种

```python
if __name__ == '__main__':
    s = QuickTest()

    # console 测试
    # s.bot.console.start()

    # 对话式测试
    s.start()

    # 快速测试单句指令
    # s.unit_test('兔兔语音阿米娅闲置')
```

```bash
python quickTest.py
```

- 实际环境的封闭测试
    - 配置封闭测试相关项后启动 Amiya
    - 之后，Amiya 仅会回应封闭测试指定的群

```yaml
account:
    group:
        # 封闭测试群号
        groupId: 362165038
        # 封闭测试：开
        closeBeta: true
setting:
    # 离线模式：开
    offline: true
```
