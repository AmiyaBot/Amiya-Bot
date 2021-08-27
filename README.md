# Amiya-Bot 4.0 Beta

> 基于 [mirai-console](https://github.com/mamoe/mirai-console) 和 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的QQ聊天机器人<br>
> 本质为一个 websocket 客户端

> 名字源于游戏 [《明日方舟》](https://ak.hypergryph.com/) 的女主角"阿米娅"，其主题与核心功能也和游戏相关。

    「博士，能再见到您……真是太好了。今后我们同行的路还很长，所以，请您多多关照！」 -- 阿米娅

> 注意：该版本仍处于测试阶段，近期可能会进行大量修改！！！

## 共生项目

- Amiya-Bot 的可视化后台管理：[Amiya-Bot-console](https://github.com/vivien8261/Amiya-Bot-console) （开发中）
- Amiya-Bot 的数据及资源文件：[Amiya-Bot-resource](https://github.com/vivien8261/Amiya-Bot-resource)

## 声明

- Amiya-Bot 是在《明日方舟》爱好者群体中诞生的以便捷功能为主的聊天机器人
- 本项目拒绝加入与金钱相关的功能，并在遵守法律法规且符合社会主义核心价值观的前提下使用
- 创建者需承诺不得使用本项目进行**任何形式的盈利行为**
- 本项目不承担因违反上述所带来的一切后果

## 鸣谢

部分功能的信息需要从各大渠道获取，特鸣谢以下网站和项目

- [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData)
- [KokodaYo](https://www.kokodayo.fun/)
- [PRTS](http://prts.wiki/)
- [明日方舟官方微博](https://m.weibo.cn/u/6279793937)
- [刀客塔的办公室](https://github.com/Rominwolf/doctors_office)

## 准备

- 想要创建自己的 Amiya，如果你不是开发者，你无需理解 Amiya 的源码。只需要你能够熟悉使用 mirai 相关套件即可。（请等待后续发布的安装包）
- 若你是开发者，建议先了解 [mirai-console](https://github.com/mamoe/mirai-console)
  以及其插件 [mirai-api-http](https://github.com/project-mirai/mirai-api-http)
  以便理解源码
    - 关于 [mirai-api-http](https://github.com/project-mirai/mirai-api-http) 的使用请到官方 Github 下查看
- 需要 python 3.7 ~ 3.8

## 部署

- 代码部署请查看[开发者文档](https://github.com/vivien8261/Amiya-Bot/blob/master/_docs/deployment.md)
- 安装包部署请等待近期发布...

## 基础群组功能

Amiya 的基础功能可以通过在群组里向 Amiya 发送`Amiya有什么功能`来获得功能指引

- 群管理员功能
- 信赖值与心情系统
- 查询干员资料
    - 基础资料
    - 精英化材料
    - 技能专精材料
    - 技能数据
    - 模组数据
    - 档案
    - 语音资料
    - 皮肤资料
- 查询敌方单位资料
- 查询材料怎么获得
- 理智恢复提醒
- 合成玉计算
- 公招查询
    - 普通标签查询
    - 图像识别
- 模拟抽卡
    - 详情模式
    - 略缩模式
- 查看明日方舟微博动态
    - 查询微博
    - 自动推送新微博

## 管理员功能

Amiya 的管理功能仅限私聊，且只有管理员能够使用 Amiya 的私聊

- 发送`重启`关键字，Amiya 将会重启
- 屏蔽用户
    - 发送`屏蔽/解除 + QQ号`，Amiya 会屏蔽或解除该用户，屏蔽后 Amiya 将不会再回应该用户的消息
- 更多功能将会陆续推出...

## 功能使用注意

- **禁言会导致 Amiya 退群！！！**
- 自然语言处理方法和公招图像识别需要调用 [百度智能云](https://cloud.baidu.com/)
  的接口，如需使用需要自行申请并配置`config.json`

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

- 为了防止打招呼时同时唤起了其他机器人回复，而其他机器人又触发了 Amiya 的回复导致循环发生，造成不可控的局面，请务必设置消息限制，在被其他机器人触发循环时及时制止

```json5
{
    "message": {
        // 10秒内最多3次指令
        "limit": {
            "seconds": 10,
            "maxCount": 3
        }
    }
}
```

## 如何维护

> 推荐搭建 [Amiya-Bot-console](https://github.com/vivien8261/Amiya-Bot-console) 获得更好的可视化维护界面<br>
> 否则部分数据维护可能需要自行到数据库修改

- Amiya 带有**自动维护**功能，会在每天凌晨4点执行以下操作：
    - 重置签到和心情值
    - 清空消息及图片记录
    - 清除图片缓存
- Amiya 在每次启动时都会**自动检查更新**。下载新数据和图片资源，请保持良好的网络环境更新。
- 在有干员增加的版本，需手动配置`configure/limitOperator.xml`添加无法通过抽卡获得的干员，否则新干员可能会被归类到可获取的干员，造成抽卡异常产出
- 部分配置改动后需重启 Amiya 后生效

## 关于 3.0 迁移到 4.0

- 4.0 版本重写了大部分核心代码并舍弃了 Mysql 数据库，已导致 3.0 的代码无法迁移。
- 4.0 在启动时会在目录下创建`amiya.db`Sqlite 数据库。内含的`user`表与旧版本`t_user`表字段一致。用户数据可以手动迁移到Sqlite

## 贡献

- 本项目欢迎 dalao 加入，拯救萌新，刻不容缓！
- 如果有更多的建议或 BUG 反馈，请提交到`issue`或官方QQ群`362165038`
- 如果你遇到项目部署问题，可以加入开发群`852191455`反馈
- 你的`star`将会成为 Amiya 成长的经验值

## TODO

- [ ] [TODO](https://github.com/vivien8261/Amiya-Bot/issues/5)
- [ ] <del>与明日方舟主题不相关的功能</del>

