# Amiya-Bot 4.0 Beta

> 基于 [mirai-console](https://github.com/mamoe/mirai-console) 和 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的QQ聊天机器人<br>
> 项目名称源于游戏 [《明日方舟》](https://ak.hypergryph.com/) 的女主角"阿米娅"，其主题与核心功能也和游戏相关。
> <br><br>注意：该版本仍处于测试阶段，近期可能会进行大量修改！！！

    「博士，能再见到您……真是太好了。今后我们同行的路还很长，所以，请您多多关照！」 -- 阿米娅

## 共生项目

共生项目为专门服务于 Amiya-Bot 的项目或资源

- Amiya-Bot 的可视化后台管理：[Amiya-Bot-console](https://github.com/vivien8261/Amiya-Bot-console)
- Amiya-Bot 的数据及资源文件：[Amiya-Bot-resource](https://github.com/vivien8261/Amiya-Bot-resource)

## 声明

- Amiya-Bot 是在 [《明日方舟》](https://ak.hypergryph.com/) 爱好者群体中诞生的以便捷娱乐功能为主的聊天机器人
- 本项目拒绝加入与金钱相关的功能，并在遵守法律法规且符合社会主义核心价值观的前提下使用
- 创建者需承诺不得使用本项目进行**任何形式的盈利行为**
- 本项目不承担因违反上述声明所带来的**一切后果**

## 鸣谢

精彩的项目背后总有强大且优秀的项目支持，没有以下项目，Amiya-Bot 将变得难以实现

- 协议支持
    - [mirai-console](https://github.com/mamoe/mirai-console)
    - [mirai-api-http](https://github.com/project-mirai/mirai-api-http)
- 数据及图片资源的下载
    - [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData)
    - [KokodaYo](https://www.kokodayo.fun/)
    - [PRTS](http://prts.wiki/)
- 信息推送
    - [明日方舟官方微博](https://m.weibo.cn/u/6279793937)
- 抽卡图片合成逻辑参考
    - [刀客塔的办公室](https://github.com/Rominwolf/doctors_office)

## 准备

- 想要创建自己的 Amiya，如果你不是开发者，仅需你能够熟悉使用 mirai 相关套件即可。
    - 安装包式部署尚未发布，请耐心等待
- 若你是开发者，建议先了解 [mirai-console](https://github.com/mamoe/mirai-console)
  以及其插件 [mirai-api-http](https://github.com/project-mirai/mirai-api-http)
  以便理解源码
    - 关于两者的使用请到官方 Github 下查看
    - 注意：本项目不负责在部署 mirai 套件时遇到的问题，请勿提交相关 issues
- 开发或代码部署需要准备 python 3.7 ~ 3.8 环境

## 部署

- 代码部署请查看[开发者文档](https://github.com/vivien8261/Amiya-Bot/blob/master/_docs/deployment.md)
- 安装包式部署请等待发布...

## [功能指引](https://github.com/vivien8261/Amiya-Bot/blob/master/_docs/function.md)

## 如何维护

> 推荐使用 [Amiya-Bot-console](https://github.com/vivien8261/Amiya-Bot-console) 获得更好的可视化维护界面，否则部分数据维护需要到数据库修改<br>
> 使用方法请阅读 [说明文档](https://github.com/vivien8261/Amiya-Bot/blob/master/_docs/console.md) <br>

- Amiya 带有 `自动维护` 功能，会在每天凌晨4点执行以下操作：
    - 重置所有用户的签到状态和心情值
    - 清空一定时间前的历史消息及图片ID记录
    - 清除本地缓存
- Amiya 在每次启动时都会执行 `更新检查`。如需更新则会下载新数据和图片资源，请保持良好的网络环境下启动。
    - Amiya 会在更新时对下载失败但不影响运行的资源作忽略处理，在第二次启动时跳过下载。如果重要的资源被忽略，请用管理员命令 `强制更新` 重新检查资源。
- 部分配置改动后需重启 Amiya 生效

## 使用注意

- 自然语言处理方法和公招图像识别需要调用 [百度智能云](https://cloud.baidu.com/)
  的接口，如需使用请自行申请并配置 `config.json`

```json5
{
    "baiduCloud": {
        "enable": true,
        "appId": "21*****7",
        "apiKey": "MM************GnL5",
        "secretKey": "XR*********************U7UM"
    }
}
```

- 为了防止某个指令会导致 Amiya 与其他机器人造成 `无限循环性回复`，造成不可控的刷屏局面，请务必设置消息限制，在与其他机器人触发循环时及时制止

```json5
{
    "message": {
        // 10 秒内最多响应 3 次指令
        "limit": {
            "seconds": 10,
            "maxCount": 3
        }
    }
}
```

## 贡献

- 本项目欢迎 dalao 加入，拯救萌新，刻不容缓！
- 如果有更多的建议或 BUG 反馈，请提交到 `issue` 或官方QQ群 `362165038`
- 如果你遇到项目部署问题，可以加入开发群 `852191455` 反馈
- 你的 `star` 将会成为 Amiya 成长的经验值

## TODO

- [ ] [更新计划](https://github.com/vivien8261/Amiya-Bot/projects/1)
- [ ] <del>与明日方舟主题不相关的功能</del>

