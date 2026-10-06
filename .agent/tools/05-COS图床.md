# COS 图床

`core/cosChainBuilder.py`：QQ 群消息里的本地临时文件（图片/语音/视频）先上传到腾讯云 COS，
再把公网 URL 交给框架。这是**运行时常驻组件**，在建立 QQ 群 bot 连接时作为默认消息链构造器注入。

相关：[01-配置.md](01-配置.md) 的 `cos_config`；[../deploy/02-打包发行.md](../deploy/02-打包发行.md) 的 `COSUploader`；
[02-工具函数.md](02-工具函数.md) 的 `run_in_thread_pool`。

---

## 1. 构造与 COS 客户端

```python
class COSQQGroupChainBuilder(QQGroupChainBuilder):        # core/cosChainBuilder.py:12
    def __init__(self, options: QQGroupChainBuilderOptions):
        super().__init__(options)
        self.cos: Optional[COSUploader] = None            # :16
        self.cos_caches = {}                              # :17

        if cos_config.secret_id and cos_config.secret_key:            # :19
            self.cos = COSUploader(
                cos_config.secret_id, cos_config.secret_key,
                logger_level=logging.NOTSET,                          # :23
            )
```

- `:6` 从 `amiyabot.adapters.tencent.qqGroup` 导入父类 `QQGroupChainBuilder` 与 `QQGroupChainBuilderOptions`。
- `:19` 只有 `secret_id` 和 `secret_key` **都非空**才创建 `COSUploader`；否则 `self.cos` 保持 `None`。
- `:7` `COSUploader` 来自 `build/uploadFile.py`——**构建/部署目录的模块被运行时导入**，属运行时代码与工具代码的耦合。
- `:23` `logger_level=logging.NOTSET`：`NOTSET` 为 0（falsy），让 `COSUploader.__init__` 跳过 `logging.basicConfig`
  ——避免运行时组件污染全局日志配置（见 [../deploy/02-打包发行.md](../deploy/02-打包发行.md)）。

---

## 2. 重写的成员

| 成员 | 行号 | 行为 |
| --- | --- | --- |
| `domain`（property） | `:26-28` | 返回 `cos_config.domain + cos_config.folder` —— **裸字符串拼接**，决定框架生成的访问域名前缀 |
| `start()` | `:30-31` | 重写为 `...`（Ellipsis），**空实现**，覆盖父类启动逻辑 |
| `temp_filename(suffix)` | `:33-38` | `super().temp_filename(suffix)` 拿 `(path, url)`；登记 `self.cos_caches[url] = f'{cos_config.folder}/{os.path.basename(path)}'`；返回原 `(path, url)` |
| `remove_file(url)` | `:40-51` | `super().remove_file(url)` 后，若 `url` 在 `cos_caches` 中则异步删除 COS 对象并摘除映射 |
| `get_image(image)`（async） | `:53-64` | 已是 `http` 开头的字符串**直接返回**；否则 `await super().get_image(image)` 后上传 |
| `get_voice(voice_file)`（async） | `:66-77` | 同 `get_image` 模式 |
| `get_video(video_file)`（async） | `:79-90` | 同 `get_image` 模式 |

三个 `get_*` 的结构一致，以 `get_image` 为例（`:53-64`）：

```python
async def get_image(self, image: Union[str, bytes]) -> Union[str, bytes]:
    if isinstance(image, str) and image.startswith('http'):
        return image                                      # :54-55 短路，不重复上传
    url = await super().get_image(image)                  # :57 父类落本地临时文件
    self.cos.upload_file(
        self.file_caches[url],                            # :60 父类维护的 URL→本地路径
        self.cos_caches[url],                             # :61 本类维护的 URL→COS key
    )
    return url
```

`get_voice`（`:66-77`）与 `get_video`（`:79-90`）是同一写法的复制，分别调 `super().get_voice` / `super().get_video`，
短路判断均为 `startswith('http')`。

---

## 3. `cos_caches` 的映射与删除时机

`cos_caches` 是 `{框架本地 URL: COS 对象键}` 字典（`:17` 初始化，`:36` 写入）。

| 阶段 | 位置 | 说明 |
| --- | --- | --- |
| **写入** | `:36` (`temp_filename`) | 父类分配临时文件路径/URL 时，同步登记它在 COS 中的目标 key |
| **读取** | `:60,73,86` | 用 `self.file_caches[url]`（父类维护的 URL→本地路径）取本地文件，以 `self.cos_caches[url]` 为远端 key 上传 |
| **删除** | `:44-51` (`remove_file`) | 父类清理本地临时文件后，**异步**删除 COS 对象并从 `cos_caches` 摘除 |

key 的构造（`:36`）：`f'{cos_config.folder}/{os.path.basename(path)}'` —— **本地文件名原样作为 COS 对象名**。

删除实现（`:44-50`）：

```python
asyncio.create_task(
    run_in_thread_pool(
        self.cos.client.delete_object,
        self.cos.bucket,
        self.cos_caches[url],
    )
)
```

因 COS SDK 同步阻塞，用 `create_task` + `run_in_thread_pool` 包成 **fire-and-forget**。

---

## 4. 依赖与调用方

**依赖** `build/uploadFile.py` 的 `COSUploader`（`:7`），直接使用其三个成员：

| 成员 | 使用位置 |
| --- | --- |
| `self.cos.client.delete_object` | `:46` |
| `self.cos.bucket` | `:47` |
| `self.cos.upload_file` | `:59,72,85` |

`COSUploader` 的详细行为（含 `upload_file` 重试 10 次后静默返回 `None` 的缺陷）
见 [../deploy/02-打包发行.md](../deploy/02-打包发行.md)。

**调用方**：`core/database/bot.py:5,112` —— `default_chain_builder=COSQQGroupChainBuilder(opt)`，
即在建立 QQ 群 bot 连接时作为默认消息链构造器注入。

---

## 5. 未启用时的行为

`cos_config.secret_id`/`secret_key` 为空时 `self.cos` 为 `None`，
但 `get_image`/`get_voice`/`get_video` **没有 `None` 检查**，会直接抛 `AttributeError`。

实践中依赖 `core/database/bot.py:109` 的 `if cos_config.activate:` 作为**外层开关**
（`bot.py:112` 在该分支内），即只有 COS 激活时才把 `COSQQGroupChainBuilder` 用起来。

**即：开关的守卫在调用方，而不在类本身**——单独实例化这个类并调用其方法是危险的。

---

## 6. 坑

- `:36` 的 key 只用 `os.path.basename(path)`，**不同子目录的同名文件会在 COS 上互相覆盖**。
- `:51` 在 `create_task` 之后**立即** `del self.cos_caches[url]`：若异步删除失败，映射已丢失，无法重试/追溯（静默泄漏 COS 对象）。
- `:28` 用裸字符串拼接，`cos_config.domain` 或 `folder` 缺尾/首斜杠会拼出非法 URL（如 `https://x.comfolder/`）。
- `:54,67,80` 的短路只判断 `startswith('http')`，`https` 恰好也被覆盖，但其它协议（`file://` 等）不会被识别。
- `:30-31` 把 `start()` 重写成空操作，若父类 `start()` 有必须的副作用会造成隐患。
- 与 [02-工具函数.md](02-工具函数.md) 的线程池共享同一全局 `executor`：
  大量图片上传会占用线程池额度，影响其它插件的阻塞调用。
