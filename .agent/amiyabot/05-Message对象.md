# 5. Message 对象

`Message` 的属性、可写字段，以及 `send` / `wait` / `wait_channel` / `recall` 的用法与语义约束。

相关：[消息构建](04-消息构建.md) · [消息与钩子](03-消息与钩子.md) · [网络与工具](08-网络与工具.md)

---

## 1. 属性表

官方文档：[接收消息](https://www.amiyabot.com/develop/basic/recvMessage.html)

| 属性 | 类型 | 释义 |
| --- | --- | --- |
| `instance` | `BotAdapterProtocol` | bot 实例 |
| `message` | `dict` | 原始消息字典 |
| `message_id` | `str` | 消息 ID |
| `message_type` | `str` | 消息类型（适用于群聊适配器） |
| `face` | `List[str]` | 消息内表情 ID 列表 |
| `image` | `List[str]` | 消息内图片 URL 列表 |
| `text` | `str` | 消息文本（**不包含触发词、中间件处理**） |
| `text_digits` | `str` | 消息文本（不含触发词、中间件处理、**中文转数字**处理） |
| `text_unsigned` | `str` | 消息文本（不含触发词、**去字符**处理） |
| `text_original` | `str` | 消息文本（**原始文本**） |
| `text_words` | `List[str]` | 消息文本分词 |
| `text_prefix` | `str` | 消息触发词 |
| `at_target` | `List[str]` | 消息内 @ 的对象列表 |
| `is_at` | `bool` | 是否 @ 机器人 |
| `is_admin` | `bool` | 是否为子频道管理员 |
| `is_direct` | `bool` | 是否是私信消息 |
| `user_id` | `str` | 用户 ID |
| `guild_id` | `str` | 频道 ID |
| `src_guild_id` | `str` | 来源频道 ID，私信下有效 |
| `channel_id` | `str` | 子频道 ID |
| `nickname` | `str` | 用户昵称 |
| `avatar` | `str` | 用户头像的 URL |
| `joined_at` | ISO8601 timestamp | 用户加入频道的时间 |
| `verify` | `Verify` | 自定义检查的结果 |
| `time` | `int` | 消息时间 |

> ⚠️ **重要变动**：从 `1.9.8` 起，若配置了前缀触发词，消息文本系列字段**不再包含**前缀，前缀被移动到 `text_prefix`。本仓库锁定 `2.1.1`，该行为已生效。

### 2.1 升到 `2.1.1` 引入的两处行为变动

**`is_at` 在 QQ 群下不再是恒 `True`**（`adapters/tencent/qqGroup/package.py`）：

| 事件 | `is_at` |
| --- | --- |
| `GROUP_AT_MESSAGE_CREATE` | `True` |
| `GROUP_MESSAGE_CREATE`（全量模式） | `False` |
| `C2C_MESSAGE_CREATE`（单聊） | `False` |

2.0.9 及以前，群聊路径**一律**把 `is_at` 置为 `True`。

本仓库影响可控：`config/prefix.yaml` 已配置前缀触发词，`factory/implemented.py` 的 `verify()` 在**前缀命中**时同样放行，与 `is_at=True` 殊途同归。但任何**依赖旧「群消息必 `is_at=True`」**的逻辑需重新核对——`pluginsDev/src/user/mainBot.py:135` 的 `(data.text_prefix or data.is_at)`、`pluginsDev/src/user/main.py:252` 的 `data.is_at or ...` 均在升级后需人工回归。

**`avatar` 改为惰性求值**（`builtin/message/structure.py:79-86`）：

```python
@property
def avatar(self):
    if not self.user_avatar and self.user_avatar_getter:
        self.user_avatar = EventLoop.run(self.user_avatar_getter)
    return self.user_avatar
```

onebot v11/v12 不再在 package 阶段 `await` 头像，而是存 `user_avatar_getter`，首次**读** `data.avatar` 时才求值。

> ✅ **在 async 处理器内读取是安全的**：`nest_asyncio` 由 `amiyautils 0.0.5` 的 `asyncioTools.py:8` 执行 `nest_asyncio.apply()`，使 `EventLoop.run` 在已运行的事件循环上可用。已在真实 2.1.1 上验证：`pluginsDev/src/user/mainBot.py:121` 的 `if data.avatar:` 正常返回 URL。
>
> ⚠️ 该安全性**依赖 `amiyautils >= 0.0.5`**（0.0.4 连 `EventLoop` 都不存在）。详见 [01-安装与导出.md](01-安装与导出.md) §1.3。

---

## 2. 本项目实际使用的属性

| 属性 | 位置 |
| --- | --- |
| `data.text` | `pluginsDev/src/replace/main.py:97`、`core/__init__.py:104` |
| `data.user_id` | `core/__init__.py:88` |
| `data.channel_id` | `core/__init__.py:89` |
| `data.message_type` | `core/__init__.py:90` |
| `data.instance.appid` | `core/__init__.py:87`、`pluginsDev/src/game/guess/guessStart.py:162` |
| `data.nickname` | `pluginsDev/src/user/main.py:190`、`user/mainBot.py:126`（读） |
| `data.at_target` | `pluginsDev/src/admin/main.py:88` |
| `data.is_admin` | `pluginsDev/src/admin/main.py:23-24`（读 + 写） |
| `data.guild_id` | `pluginsDev/src/replace/main.py:93` |
| `data.avatar` | `pluginsDev/src/user/main.py:100` 附近 |

**`Message` 字段可写**：`data.is_admin = ...`（`admin/main.py:24`）、`data.nickname = ...`（`user/main.py:239`）。

> ⚠️ 字段改写要趁早。`is_admin`、`nickname` 都在 `message_created` 里改写；**越晚改写，越可能已被其他插件读取**。

---

## 3. 方法一览

| 方法名 | 参数 | 释义 | 异步 |
| --- | --- | --- | --- |
| `send` | `reply` | 发送一条消息 | 是 |
| `wait` | `reply, force, max_time, data_filter` | 等待用户消息 | 是 |
| `wait_channel` | `reply, force, clean, max_time, data_filter` | 等待子频道消息 | 是 |
| `recall` | — | 撤回消息 | 是 |

`data.verify` 由 `@bot.on_message(verify=...)` 赋值（`Verify` 对象，见 [消息与钩子](03-消息与钩子.md) 第 4.3 节）。

---

## 4. `data.send(chain)`

`pluginsDev/src/user/main.py:64`：

```python
await data.send(Chain(data).text('昵称审核中，请稍等...'))
```

---

## 5. `data.wait(chain, force=...)`

`pluginsDev/src/arknights/recruit/main.py:305`：

```python
wait = await data.wait(Chain(data, at=True).text('博士，请发送您的公招界面截图~'), force=True)
```

参数（[创建连续对话](https://www.amiyabot.com/develop/basic/continuityMessage.html)）：

| 参数名 | 类型 | 释义 | 默认值 |
| --- | --- | --- | --- |
| `reply` | `Chain` | Chain 对象 | — |
| `force` | `bool` | 使用强制等待 | `False` |
| `max_time` | `int` | 最长等待时间（秒数） | `30` |
| `data_filter` | `Callable` | Message 过滤器 | — |
| `level` | `int` | 优先级 | `0` |

**关键语义**：

- 超时返回 `None`。
- 同一子频道同一用户只能存在一个等待事件；新等待创建会注销旧的并抛 `WaitEventCancel` 异常。
- 非 `force` 时，**仅在不能触发任何其他功能**时消息才返回到等待处。
- 在等待时间内使用其他功能，等待也会被注销。

> ⚠️ `WaitEventCancel` 会**终止进行中的业务**，这是预期行为，通常由全局异常捕捉器过滤。

---

## 6. `data.wait_channel(...)`

简用（`pluginsDev/src/game/wordle2/main.py:32`）：

```python
event = await data.wait_channel(Chain(data).text(main_text), force=True)
```

全参数（`pluginsDev/src/game/wordle2/gameStart.py:50`）：

```python
event = await data.wait_channel(ask, force=True, clean=True, max_time=5, data_filter=guess_filter)
```

类型注解（`pluginsDev/src/game/guess/guessStart.py`）：

```python
from amiyabot.builtin.message import ChannelMessagesItem
```

参数：

| 参数名 | 类型 | 释义 | 默认值 |
| --- | --- | --- | --- |
| `reply` | `Chain` | Chain 对象 | — |
| `force` | `bool` | 使用强制等待 | `False` |
| `clean` | `bool` | 是否清空消息列表 | `True` |
| `max_time` | `int` | 最长等待时间（秒数） | `30` |
| `data_filter` | `Callable` | Message 过滤器 | — |
| `level` | `int` | 优先级 | `0` |

**返回 `ChannelMessagesItem`**（非 `Message`）：

| 属性 | 类型 | 释义 |
| --- | --- | --- |
| `event` | `ChannelWaitEvent` | 等待事件的实例 |
| `message` | `Message` | Message 对象 |

方法 `close_event()`（**非异步**）关闭等待事件。

> ⚠️ **该方法不可用于支持私信的功能里**。
>
> ⚠️ `wait_channel` 返回后**不会**自动关闭事件，业务结束时**必须**调用 `close_event()`，否则会持续拦截子频道消息直至超时。

仓库中通过 `event.message` 取回复消息（`pluginsDev/src/game/guess/main.py:66` 之后的过滤逻辑）。

---

## 7. `data.recall()`

无参数异步方法，用于撤回消息。本仓库无直接调用点，用法见 [撤回消息](https://www.amiyabot.com/develop/basic/recallMessage.html)。
