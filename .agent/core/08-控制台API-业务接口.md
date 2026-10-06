# core 运行时 · 控制台 API：业务接口

本文覆盖 `gacha`（6 端点）、`plugin`（9 端点，重点是 install/upgrade 与回滚）、`replace`（9 端点）、`opterator`（4 端点）。

注册机制、参数模型、`allow_path` 白名单与 `admin`/`bot`/`user`/`dashboard` 见 [控制台 API · 机制与基础接口](07-控制台API-机制与基础接口.md)。

相关：[插件加载器](02-插件加载器.md) · [插件配置 · 基础](03-插件配置-基础.md) · [数据库 · 总览与核心表](05-数据库-总览与核心表.md) · [常见问题](09-常见问题.md)

---

## 1. `gacha.py`（79 行，6 个端点，含 1 个免鉴权端点）

### 1.1 `PoolModel`（`:9-16`）

`PoolModel`（`:9-16`）字段为 `id`（`None`）、`pool_name: str`、`pickup_6`/`pickup_5`/`pickup_4`/`pickup_s`（均 `Optional[str] = ''`）、`limit_pool: int`。

- **只暴露了 5 个 pickup 字段**（`:12-15`），**没有 `pickup_6_rate` 等概率字段，也没有 `pickup_s_5`/`s_4`/`s_3`**。
  - 对比 `Pool` 表（`core/database/bot.py:216-238`）有 `pickup_6/5/4/3/2/1` + 各自 `_rate` + `pickup_s/_s_5/_s_4/_s_3/_s_2/_s_1`——**共 18 个 pickup 相关字段**。
  - **控制台只能编辑这 5 个字段**，其余靠同步（`sync_pool`）或直接改库。
- **`add_pool` 与 `update_pool` 都用 `data.dict()`**（`:41`、`:52`）——**直接展开整个模型**：
  ```python
  Pool.create(**data.dict())                                        # :41
  Pool.update(**data.dict()).where(Pool.id == data.id).execute()    # :52
  ```
  - **`add_pool`**：`data.dict()` **包含 `id`**（`:10`，默认 `None`），传给 `Pool.create` 时 `id=None` 表示自增，能工作。
  - **字段默认一致**：`Pool.limit_pool`（`core/database/bot.py:188`）必填无默认，`PoolModel.limit_pool` 也必填（`:16`）✅；`Pool.is_classicOnly`/`is_official` 有默认值（`:199`、`:203`），不会被 `data.dict()` 覆盖 ✅。
  - **`update_pool`**：peewee 的 `update(**kwargs)` 只更新传入的列，所以模型里没有的字段（`pool_uuid`、`pool_image` 等）**不会被覆盖**。但 `id` 会进入 SET 子句（把自己设成自己，无害）。

### 1.2 端点清单

| 方法 | 路径 | 行号 | HTTP | 参数 | 业务规则 |
| --- | --- | --- | --- | --- | --- |
| `get_pool` | `*getPool` | `:21-34` | 默认 | `QueryData` | 分页 + 5 字段模糊搜索，`order_by(Pool.id.desc())` |
| `add_pool` | `*addPool` | `:36-43` | 默认 | `PoolModel` | **重名 500** |
| `update_pool` | `*updatePool` | `:45-54` | 默认 | `PoolModel` | **重名且非自身 500** |
| `delete_pool` | `*deletePool` | `:56-60` | 默认 | `PoolModel` | 按 `id` 删 |
| `sync_pool` | `*syncPool` | `:62-71` | **`get`** | 无 | **调插件同步卡池** |
| `get_gacha_pool` | **`/pool/getPool`** | `:73-78` | **`get`** | 无 | 🔓 **免鉴权白名单端点** |

**`get_pool` 的搜索（`:25-32`）**：5 个字段 `OR` 连接（`pool_name` / `pickup_6` / `pickup_5` / `pickup_4` / `pickup_s`），排序 `Pool.id.desc()`（`:23`）——**最新添加的在前**。

### 1.3 `update_pool` 的重名检查（`:47-50`）

检查逻辑（`:47-50`）是 `pool = Pool.get_or_none(pool_name=data.pool_name)`（`:47`）后直接判 `if pool.id != data.id`（`:49`）并返回 500「卡池已存在」（`:50`）。

- `:47` 查的是「新名字对应的池子」，`:49` 判断它的 id 是否等于要改的 id。
- ⚠️ **如果 `data.pool_name` 在库里不存在**，`pool` 是 `None`，`pool.id` 会 **`AttributeError`**（`:49`）——**真实的崩溃路径**。触发条件：把卡池改名成一个**全新名字**（库里没有同名记录）。
  - **正确写法应该是先判 `if pool and pool.id != data.id`**。对比 `core/server/bot.py:80` 的 `if exists and exists.id != data.id` ——**那里写了 `exists and`，这里漏了**。
  - **绕过办法**：改卡池名时要么保持同名，要么先确认新名字已存在；改名的安全做法是直接改库或删了重建。
- **只能按 id 定位**（`Pool.update(...).where(Pool.id == data.id)`，`:52`），所以 `PoolModel.id` 必须传。

**`delete_pool`（`:56-60`）**：直接按 id 删，**无存在性检查**。注意 `:60` 的 `f'删除成功'` 是**没有占位符的 f-string**（无害但多余）。

### 1.4 `sync_pool` — 插件反向调用（`:62-71`）

流程（`:62-71`）：插件未装则 500「尚未安装此插件」（`:64-65`）；否则 `getattr(bot.plugins['amiyabot-arknights-gacha'], 'sync_pool')`（`:67`）后 `await sync_pool(force=True)`（`:68`），按返回值给「同步成功」（`:70`）或 500「同步失败」（`:71`）。

- **宿主的职责边界**：宿主**不知道**抽卡逻辑，它只做「检查插件是否安装 → 通过 `getattr` 拿方法 → 调用」。
- **`bot.plugins` 是 `plugin_id -> 实例` 的字典**（amiyabot 提供），用字符串 key 直接查。
- **`getattr(instance, 'sync_pool')`（`:67`）没有默认值**——若插件没定义该方法会 `AttributeError`（500）。由插件契约保证：`pluginsDev/src/arknights/gacha/main.py:34-51` 的 `GachaPluginInstance.sync_pool` 就是被调的那个方法。
- **`force=True`（`:68`）** 强制忽略本地已有卡池数据重新同步。插件侧实现（`gacha/main.py:35-51`）是**先全删再全插**：`:45` `OperatorConfig.delete()`、`:46` `Pool.delete()`、`:48-49` `batch_insert`。
  ⚠️ **同步过程中若失败，卡池数据会丢失**（已删未插）。

### 1.5 `/pool/getPool` — 免鉴权白名单端点（`:73-78`）

它把 `query_to_list(Pool.select())`（`:76`）与 `query_to_list(OperatorConfig.select())`（`:77`）组装成 `{'Pool': ..., 'OperatorConfig': ...}` 一并返回。

- **是 `allow_path` 三个白名单之一**（`core/__init__.py:34`），**无需鉴权即可访问**，服务对象见 [机制与基础接口 · allow_path](07-控制台API-机制与基础接口.md#7-allow_path-白名单三个路径分别服务谁)。
- **无分页、无过滤**，一次性返回**全表**（`Pool` 与 `OperatorConfig`）。
- **消费方是远端插件商店**：远端拉取 `OperatorConfig` 后，再由 gacha 插件通过 `sync_pool`（`pluginsDev/src/arknights/gacha/main.py:33-49`）拉回本地 `Pool`/`OperatorConfig` 表。**链路：控制台 → 插件商店 → 用户端插件 → 本地库**。
- ⚠️ **安全提示**：它免鉴权且返回全表，**任何人只要能访问 `host:port` 就能拿到卡池数据与干员配置**。这是有意的（供官方服务端拉取），但部署时**不要把控制台端口直接暴露到公网**。

---

## 2. `plugin.py`（199 行，9 个端点）

控制台插件管理的全部实现。

### 2.1 模型（`:15-47`）

| 模型 | 行号 | 字段 |
| --- | --- | --- |
| `GetConfigModel` | `:15-16` | `plugin_id: str` |
| `SetConfigModel` | `:19-22` | `plugin_id: str`、`config_json: str`、`channel_id: str = None` |
| `DelConfigModel` | `:25-27` | `plugin_id: str`、`channel_id: str` |
| `InstallModel` | `:30-32` | `url: str`、`packageName: str` |
| `UpgradeModel` | `:35-38` | `url: str`、`packageName: str`、`plugin_id: str` |
| `UninstallModel` | `:41-42` | `plugin_id: str` |
| `ReloadModel` | `:45-47` | `plugin_id: str`、`force: bool = False` |

**设计模式**：每个端点一个专用模型，而不是复用一个通用模型——比 `core/server/bot.py` 的继承式更啰嗦但更清晰。

**`InstallModel` / `UpgradeModel` 用 `url` + `packageName` 二元组**（`:31-32`、`:36-37`），而不是直接传文件名——**URL 由前端从插件商店拿到**，`packageName` 是落盘文件名。

### 2.2 `use_loader` — 共用的装载辅助（`:50-57`）

它（`:50-57`）新建 `PluginsLoader(bot)`（`:51`），调 `load_plugin_file(plugin)`（`:52`），成功后手工登记到 `loader.plugins[load_res.plugin_id]`（`:54`）、跑 `check_requirements`（`:55`）、返回 `install_loaded_plugins()`（`:56`）；失败返回 `0`（`:57`）。

**这是 install / upgrade 两个端点的共同核心**：

- **新建一个 `PluginsLoader` 实例**（`:51`）——**不复用启动时的 loader**（`amiya.py:13` 的局部变量早已离开作用域）。所以控制台安装的插件走的是**全新的 loader 实例**，但共用同一个 `bot` 单例。
- **手工走启动流程的三步**（`:52`、`:55`、`:56`），顺序与 `load_local_plugins`（`core/plugins/__init__.py:22-36`）一致，但**跳过了目录扫描和 `os.walk`**——因为文件路径是直接传进来的。
- **`:54` 手工塞进 `loader.plugins`**：因为 `load_plugin_file` 只返回实例，不会自动登记（对比 `core/plugins/__init__.py:28` 在扫描时做的登记）。
- **`:55` 做依赖检查**——所以控制台安装的插件**同样会自动补拉缺失依赖**。
- **返回 `install_loaded_plugins()` 的结果（安装数量 int）**，失败时返回 `0`（`:57`）。**调用方用 `if await use_loader(...)` 做真假判断**（`:154`、`:173`）——因为 `0` 是假值。
- `:51` 每次新建 loader，其 `self.plugins` 初始为空（`core/plugins/__init__.py:20`），所以 `check_requirements` 的 `exists` 集合主要来自 `self.bot.plugins`（`core/plugins/__init__.py:78`），即**已安装的插件**。这是正确的。

### 2.3 插件列表与配置端点

| 方法 | 路径 | 行号 | HTTP | 入参 | 返回 |
| --- | --- | --- | --- | --- | --- |
| `get_installed_plugin` | `*getInstalledPlugin` | `:62-86` | **`get`** | 无 | 已装插件清单 |
| `get_plugin_default_config` | `*getPluginDefaultConfig` | `:88-97` | 默认 | `GetConfigModel` | 插件的 default/schema |
| `get_plugin_config` | `*getPluginConfig` | `:99-111` | 默认 | `GetConfigModel` | 频道的配置字典 |
| `del_plugin_config` | `*delPluginConfig` | `:113-120` | 默认 | `DelConfigModel` | 删一条配置 |
| `set_plugin_config` | `*setPluginConfig` | `:122-144` | 默认 | `SetConfigModel` | 写配置 |

**`get_installed_plugin`（`:62-86`）** 遍历 `bot.plugins.items()`（`:66`），为每个插件组装：

logo 的算法（`:68-70`）：`item.path` 非空时取 `item.path[-1]`（`:69`），再 `'/' + os.path.relpath(os.path.join(item_path, 'logo.png')).replace('\\', '/')`（`:70`）。

字段为 `name`（`:74`）、`version`（`:75`）、`plugin_id`（`:76`）、`plugin_type`（`:77`）、`description`（`:78`）、`document`（`:79`）、`instruction`（`:80`）、`logo`（`:81`）、`allow_config`（`:82`）。

- **`item.path` 是列表，取 `[-1]`**（`:69`）——从 `:170` 的 `copy.deepcopy(bot.plugins[...].path)` 与 `:175-179` 的 `for item in old_plugin_path` 可确认它是**可迭代的路径列表**。
- **`logo` 是 URL 路径**（`:70`）：`os.path.relpath(解压目录/logo.png)` 转成 `/` 分隔的路径，**拼上前导 `/`**。它指向 `app.add_static_folder('/plugins', 'plugins')` 挂载的静态目录（`core/__init__.py:41`）——**logo 必须在插件的 `plugins/` 子目录里有 `logo.png`**。`.replace('\\', '/')` 是 **Windows 兼容**处理。**若插件没有 `logo.png`**，`logo` 字段仍会是路径字符串，但访问时 404（**没有存在性检查**）。
- **`check_file_content`（`:79-80`）**：把「路径」转成「内容」——若 `document` 是文件路径就读取，否则原样返回（实现 `core/util/common.py:52-57`）。
- **`instruction` 用 `hasattr` 保护**（`:80`）：原生 `PluginInstance` 没有这个属性，只有 `AmiyaBotPluginInstance` 才有。
- **`allow_config`（`:82`）** 的判据是 `isinstance(item, AmiyaBotPluginInstance)`。原生插件在控制台里配置面板会隐藏。

**`get_plugin_default_config`（`:88-97`）**：直接调 `plugin.get_config_defaults()`（`:95`），返回 4 个 JSON 字符串。**非 `AmiyaBotPluginInstance` 返回空响应**（`:97`）。

**`get_plugin_config`（`:99-111`）**：查 `PluginConfiguration.select().where(plugin_id == ...)`（`:105-107`），返回 `{item.channel_id: item.json_config}`（`:109`）——**`json_config` 是未解析的 JSON 字符串**（前端自己解析），且**包含全局那条记录**，其 key 是 `''`。

**`set_plugin_config`（`:122-144`）**：先 `bot.plugins.get(data.plugin_id)`（`:124`），未装则 500「未安装该插件」（`:126`）；再 `PluginConfiguration.get_or_none(plugin_id=..., channel_id=...)`（`:128-130`），不存在就 `create(..., version=plugin.version)`（`:137`），否则改 `config.version`（`:140`）与 `config.json_config`（`:141`）后 `save()`。

- ⚠️ **`config_json` 是字符串，原样存库，不做 JSON 解析、不做 Schema 校验**（`:135`、`:141`）——**前端传入非法 JSON 也会被存进去**，之后插件读取时会 `json.JSONDecodeError`，触发「重置为默认值」路径（`amiyaBotPluginInstance.py:98-101`）。
- ⚠️ **写入时更新 `version`（`:137`、`:140`）**——与 `set_config` 同样的坑：**抢先提版本号，跳过下次的 `merge_dict` 升级**。
- ⚠️ **`channel_id` 可为 `None`**（`SetConfigModel` 里 `channel_id: str = None`，`:22`），但 `PluginConfiguration.channel_id` 是**非空字段**（`core/database/plugin.py:17`）。**正确用法是全局配置传 `''`**（对应 `global_config_channel_key`）。这是容易搞错的 API 约定。

**`del_plugin_config`（`:113-120`）**：按 `(plugin_id, channel_id)` 删除，**无存在性检查**，返回空成功。

### 2.4 `install_plugin`（`:146-159`）

流程（`:146-159`）：

1. **`download_async(url)` 下载**（`:148`）——URL 来自前端。
2. **落盘到 `plugins/{packageName}`**（`:150-152`）——用 `mode='wb+'`（`:151`，读写模式，实际只写）。**文件名完全由 `packageName` 决定，没有做路径穿越校验**（**安全提示**：`packageName` 含 `../` 会写到目录外；这是内网控制台，风险可接受但值得知道）。
3. **`use_loader(plugin)` 装载**（`:154`）。
4. 失败时**不删除已落盘的文件**（`:157`）——**半成品 zip 会留在 `plugins/` 目录里**，下次启动 `load_local_plugins` 会再扫到它并尝试加载（失败则记日志）。

⚠️ **没有「已安装即拒绝」的检查**——重复安装同一插件时，`use_loader` 内部的 `install_loaded_plugins` 会因 `plugin_id in self.bot.plugins` 而跳过（`core/plugins/__init__.py:47-48`），返回 `count=0`，于是 `install_plugin` 会返回 **500「插件安装失败」**——**实际上已经装好了**。这是误导性的错误信息。

### 2.5 `upgrade_plugin` — 升级与回滚（`:161-187`）

**全部端点里唯一带失败回滚的**：

| 步骤 | 行号 | 说明 |
| --- | --- | --- |
| ① 下载新包 | `:163` | 失败 → 500「插件下载失败」（`:187`） |
| ② 落盘 | `:165-167` | 新 zip 先写到 `plugins/{packageName}` |
| ③ **深拷贝旧路径** | `:170` | **必须在 uninstall 之前拷贝**，否则路径信息随插件实例一起消失 |
| ④ **卸载旧插件** | `:171` | `bot.uninstall_plugin(plugin_id)`，**没有 `remove=True`**——**只从内存摘除，不删文件** |
| ⑤ 装载新插件 | `:173` | 走 `use_loader` |
| ⑥ 成功 → 删旧文件 | `:175-179` | 逐个判断目录/文件 |
| ⑦ 失败 → **回滚** | `:183-184` | 删掉新 zip，**用旧路径重新安装** |

**为什么 `:171` 不传 `remove=True`**：`uninstall_plugin(plugin_id)` 只从 `bot.plugins` 移除，**保留磁盘文件**——这正是为了让 `:184` 的回滚能重新安装旧插件。如果 `:171` 就删了文件，回滚就没素材了。对比卸载端点（`:190-193`）传了 `remove=True`（`:191`），因为那里是**真卸载**。

**`copy.deepcopy`（`:170`）的必要性**：`bot.plugins[id].path` 是列表，uninstall 后实例可能被销毁，深拷贝一份保住路径。

**`:175-179` 的删除逻辑**：遍历旧插件的**全部路径**（可能是解压目录 + zip 文件），用 `os.path.isdir` 判断——目录用 `rmtree`，文件用 `remove`。

**回滚的缺口**：

1. ⚠️ **回滚不恢复配置**：`uninstall_plugin`（`:171`）虽不删文件，但**插件实例的构造副作用**（配置升级）已经发生过。回滚后重装旧版插件时，`compare_version_numbers(库里的新版本, 旧插件版本) < 0` **为假**（库里更新），所以**不做降级**——用户配置保留，但可能与旧插件代码不兼容。**这是升级回滚最隐蔽的坑。**
2. ⚠️ **`old_plugin_path[0]` 可能不是 zip 文件**——如果 `path[0]` 是解压后的目录，`install_plugin(目录, extract_plugin=True)` 的行为取决于框架实现。
3. ⚠️ **`:184` 的返回值没检查**——回滚失败也无法感知，仍返回「插件更新失败」（`:185`）。
4. ⚠️ **没有 try/except**：若 `:163-184` 之间任何一步抛异常（如 `bot.plugins[data.plugin_id]` 的 `KeyError`，`:170`），**端点直接 500 且不执行回滚**。**调用前必须确保 `plugin_id` 确实已安装**（前端负责）。
5. **`:170` 的 KeyError 风险**：若 `data.plugin_id` 不在 `bot.plugins` 里会抛 `KeyError`——**不过此时新 zip 已经落盘**（`:166-167`），会留下残留文件。

### 2.6 `uninstall_plugin`（`:189-193`）与 `reload_plugin`（`:195-199`）

`uninstall_plugin`（`:189-193`）就是 `bot.uninstall_plugin(data.plugin_id, remove=True)`（`:191`）；`reload_plugin`（`:195-199`）就是 `bot.reload_plugin(data.plugin_id, force=data.force)`（`:197`）。

- **`uninstall_plugin` 传 `remove=True`**（`:191`）——**真删磁盘文件**。与 upgrade 的 `:171`（不删）形成对比。
- **两者都不做存在性检查**：卸载未安装的插件、重载未安装的插件，都会返回「成功」消息（`:193`、`:199`）。
- **`reload_plugin` 的 `force` 参数**（`:197`）：`ReloadModel.force` 默认 `False`（`:47`）。force 的具体语义取决于框架实现。
- **两个端点都没有 try/except**——`bot.uninstall_plugin` / `bot.reload_plugin` 抛异常会直接 500。
- **卸载不会清理配置**：`PluginConfiguration` 记录仍在库里（宿主没删）。**重装同一插件时，旧配置会「复活」**（因为 `plugin_id` 相同）。从 `del_plugin_config` 端点（`:113-120`）独立存在来看，**清理配置是用户的手动操作**。

---

## 3. `replace.py`（102 行，9 个端点，含 1 个免鉴权端点）

### 3.1 模型（`:10-21`）

`ReplaceModel`（`:10-15`）：`id`、`origin: str`、`replace: str`、`is_global`、`is_active`（后两者默认 `None`）。`ReplaceSettingModel`（`:17-21`）：`id`、`text: str`、`status: int`。

**`ReplaceModel` 只暴露 5 个字段**，而 `TextReplace` 表有 8 个（`core/database/bot.py:245-252`）。缺失的是 `user_id`/`group_id`/`in_time`/`is_user_only`——**`add_replace` 在服务端硬编码这些值**（`:41-48`）：`user_id='0'`、`group_id='0'`、`in_time=int(time.time())`、`is_global=1`、`is_active=1`。

**结论：控制台只能管理「全局替换」（`is_global=1`）**，用户/群级替换由插件自己管理。

### 3.2 端点清单

| 方法 | 路径 | 行号 | HTTP | 入参 | 业务规则 |
| --- | --- | --- | --- | --- | --- |
| `get_replace` | `*getReplace` | `:26-33` | 默认 | `QueryData` | 分页 + origin/replace 模糊搜索，`order_by(id.desc())` |
| `add_replace` | `*addReplace` | `:35-50` | 默认 | `ReplaceModel` | **重复全局替换 500** |
| `update_replace` | `*updateReplace` | `:52-56` | 默认 | `ReplaceModel` | 按 id 更新 |
| `delete_replace` | `*deleteReplace` | `:58-62` | 默认 | `ReplaceModel` | 按 id 删 |
| `get_replace_setting` | `*getReplaceSetting` | `:64-66` | **`get`** | 无 | 全量标签列表 |
| `add_replace_setting` | `*addReplaceSetting` | `:68-75` | 默认 | `ReplaceSettingModel` | **标签重复 500** |
| `delete_replace_setting` | `*deleteReplaceSetting` | `:77-81` | 默认 | `ReplaceSettingModel` | 按 id 删 |
| `sync_replace` | `*syncReplace` | `:83-92` | **`get`** | 无 | 调插件同步 |
| `get_global_replace` | **`/replace/getGlobalReplace`** | `:94-102` | **`get`** | 无 | 🔓 **免鉴权白名单端点** |

**`add_replace` 的重复检查（`:37-38`）**：

即 `TextReplace.get_or_none(origin=data.origin, replace=data.replace, is_global=1)` 命中就返回 500「全局替换已存在」。

- **三个条件联合查询**（origin + replace + is_global），即「同一对替换关系」，`is_global=1` 与 `:46` 的写入一致。
- ⚠️ **但不检查 `is_active`**——所以「已停用的同名替换」也会被判定为重复，**无法再添加**。功能性缺陷。

**`update_replace`（`:52-56`）的坑**：

实现是 `TextReplace.update(**data.dict()).where(TextReplace.id == data.id).execute()`。

- ⚠️ **`data.dict()` 含 `is_global=None` 与 `is_active=None`**（模型默认 `None`，`:14-15`）——**若前端不传这两个字段，它们会被设为 NULL**！
- `TextReplace.is_global` 是 `IntegerField(default=0)`（`core/database/bot.py:251`），**`null` 约束未声明**。写入 NULL 在 SQLite 下可行，但之后 `get_global_replace` 的 `is_global == 1` 过滤（`:96`）就**匹配不到该记录**——**更新一次就可能让全局替换从白名单端点消失**。
- **前端必须始终传 `is_global` 与 `is_active`。**

**`sync_replace`（`:83-92`）**：与 `sync_pool` 结构完全一致的插件反向调用——`:85` 检查 `'amiyabot-replace' not in bot.plugins`，`:88` `getattr(bot.plugins['amiyabot-replace'], 'sync_replace')`，`:89` `await sync_replace(force=True)`。同样的 `getattr` 无默认值模式。插件实现见 `pluginsDev/src/replace/main.py`。

### 3.3 `/replace/getGlobalReplace` — 免鉴权白名单端点（`:94-102`）

它 `query_to_list(TextReplace.select().where(TextReplace.is_global == 1, TextReplace.is_active == 1))`（`:96`），再把每条记录的 `user_id`（`:99`）与 `group_id`（`:100`）改写为 `'0'`。

- ⭐ **它用的是 `@app.route(method='get')` 而非显式路径**（`:94`），但白名单里写的是 `/replace/getGlobalReplace`（`core/__init__.py:33`）——**这证明框架自动把方法名 `get_global_replace` 转成了驼峰路径 `getGlobalReplace`**，否则这条白名单就是无效的。这是路由转换规则最硬的证据（见 [机制与基础接口 · 路由路径](07-控制台API-机制与基础接口.md#13-路由路径的生成规则)）。
- **开发含义**：新增免鉴权接口时，白名单里必须写**驼峰**形式；而定义端点时可以继续用蛇形方法名——两者由框架自动桥接。
- **两个硬编码过滤条件**（`:96`）：`is_global == 1` **且** `is_active == 1`——只返回启用中的全局替换。
- **`:98-100` 强制改写 `user_id`/`group_id` 为 `'0'`**——即使数据库里存了别的值也覆盖。这是给下游用的数据净化：确保消费方拿到的一定是「全局替换」语义。
- **无分页，返回全量**——与 `/pool/getPool` 同属「供远端服务拉取的清单接口」。

---

## 4. `opterator.py`（50 行，4 个端点）

> **文件名拼写**：文件是 `opterator.py`（**少了一个 `a`**，正确拼写应为 `operator`），类名是 `Operator`（`:15`）。这是历史拼写错误，导入时路径必须写 `core.server.opterator`（`core/server/__init__.py:1`）。要与 `OperatorIndex`/`OperatorConfig` 两张表区分开。

### 4.1 `OperatorConfigModel`（`:9-11`）

`OperatorConfigModel`（`:9-11`）只有 `name: str`（`:10`）与 `operator_type: int`（`:11`）。

**字段名是 `name`**（`:10`），而表字段是 `operator_name`（`core/database/bot.py:164`）——**转换在 `set_operator` 里手工完成**（`:37-42`）。

### 4.2 端点清单

| 方法 | 路径 | 行号 | HTTP | 入参 | 业务规则 |
| --- | --- | --- | --- | --- | --- |
| `get_all_operator` | `*getAllOperator` | `:16-18` | **`get`** | 无 | 全量 `OperatorIndex` |
| `get_operator` | `*getOperator` | `:20-33` | 默认 | `QueryData` | **索引 + 配置左连接**，分页 |
| `set_operator` | `*setOperator` | `:35-44` | 默认 | `OperatorConfigModel` | **有则 update，无则 create** |
| `update_setting` | `*updateSetting` | `:46-50` | **`get`** | 无 | **重新初始化游戏数据** |

**`get_all_operator`（`:16-18`）**：`query_to_list(OperatorIndex.select())`——**全表、无分页**。用于前端干员选择器（需要完整列表）。

**`get_operator`（`:20-33`）— 左连接**：

它以 `OperatorIndex.select(OperatorIndex, OperatorConfig).join(OperatorConfig, 'left join', on=(OperatorConfig.operator_name == OperatorIndex.name))`（`:22-26`）起手；有 `data.search` 时再按 `name.contains(...) | en_name.contains(...)` 过滤（`:30-31`）。

- **连接条件是 `OperatorConfig.operator_name == OperatorIndex.name`**（`:25`）——注意**左边是配置表的 `operator_name`，右边是索引表的 `name`**，字段名不同。
- **左连接**保证「没有配置记录的干员也出现在列表里」（此时 `operator_type` 为 NULL）。
- **搜索匹配中文名与英文名**（`:30-31`）。
- ⚠️ **无 `order_by`**——顺序由数据库决定，**不稳定**（分页时可能出现跨页重复）。

**`set_operator`（`:35-44`）— 手工 upsert**：

即 `if OperatorConfig.get_or_none(operator_name=data.name)`（`:37`）时执行 `update(operator_type=...).where(operator_name == data.name)`（`:38-40`），否则 `create(operator_name=..., operator_type=...)`（`:42`）。

- **手工实现「查到就 update、否则 create」**，而不是用 `get_or_create` 后赋值——**避免 `create` 失败时的半个对象**。
- **`data.name` → `operator_name=data.name` 的字段名转换**（`:37`、`:39`、`:42`）。
- **`OperatorConfig` 表没有唯一约束**（`core/database/bot.py:164`），所以**并发下可能插入重复行**，这里没有防护。

**`update_setting`（`:46-50`）— 手动重载游戏数据**：

它就是依次调 `ArknightsConfig.initialize()`（`:48`）与 `ArknightsGameData.initialize()`（`:49`）后返回「更新成功」（`:50`）。

- **`core/server/opterator.py:4` 从 `core.resource.arknightsGameData` 导入这两个类**。
- **这两个 `initialize()` 是「遍历并调用注册的初始化函数」**（实现 `core/resource/arknightsGameData.py:26-29` 与 `:61-64`）：
  ```python
  @classmethod
  def initialize(cls):
      for method in cls.initialize_methods:
          method(cls)
  ```
- **注册是插件干的**（`initialize_methods` 是类变量列表）：`ArknightsConfig.initialize_methods = [config_initialize]`（`pluginsDev/src/arknights/arknightsGameData/builder/common.py:113`）、`ArknightsGameData.initialize_methods = [gamedata_initialize]`（`pluginsDev/src/arknights/arknightsGameData/builder/__init__.py:395`）。
- **本质是「通知 gamedata 插件重新解析本地数据」**——一个**插件反向调用**（宿主 → 插件），但走的是**类变量注册**而非 `getattr`（对比 §1.4 的 `sync_pool`）。
- **`ArknightsConfig` 必须先于 `ArknightsGameData`**（`:48-49`）——因为配置定义了 `limit`/`unavailable` 等基础分类，数据解析要依赖它们。
- ⚠️ **如果 gamedata 插件没装**，`initialize_methods` 是**空列表**（`core/resource/arknightsGameData.py:24`、`:59` 的初值），`initialize()` 什么都不做，**端点仍返回「更新成功」**——误导性的成功响应。
- ⚠️ **这是同步阻塞调用**，数据量大时可能耗时较久（`gamedata_initialize` 会解析大量 JSON），**期间会阻塞事件循环**。

---

## 5. 端点总表

**共 8 个控制器、44 个 `@app.route` 装饰器**（`grep -rc "@app.route" core/server/*.py` 合计 44），其中 43 个是 HTTP 端点、另加 1 个静态目录挂载（`/plugins`）。下表中 `*` 表示**由方法名 snake→camel 推导**，加粗表示**显式声明或免鉴权**。

| # | 控制器 | 路径 | HTTP | 功能 |
| --- | --- | --- | --- | --- |
| 1 | `Admin` (`admin.py`) | **`/`** | GET | 跳转 `/docs` |
| 2 | `Admin` | `*getAdmin` | 默认 | 管理员分页列表 |
| 3 | `Admin` | `*addAdmin` | 默认 | 加管理员 |
| 4 | `Admin` | `*deleteAdmin` | 默认 | 删管理员 |
| 5 | `Bot` (`bot.py`) | `*link` | GET | 连通性探针 |
| 6 | `Bot` | `*getAllBot` | GET | 账号列表 + `running`/`alive` |
| 7 | `Bot` | `*addBot` | 默认 | 加账号 |
| 8 | `Bot` | `*editBot` | 默认 | 改账号 |
| 9 | `Bot` | `*runBot` | 默认 | 运行期启动 |
| 10 | `Bot` | `*stopBot` | 默认 | 运行期停止 |
| 11 | `Bot` | `*deleteBot` | 默认 | 停止 + 删记录 |
| 12 | `User` (`user.py`) | `*getUser` | 默认 | 用户三表左连接分页 |
| 13 | `User` | `*editUser` | 默认 | 改 black/jade_point/coupon |
| 14 | `Gacha` (`gacha.py`) | `*getPool` | 默认 | 卡池分页 |
| 15 | `Gacha` | `*addPool` | 默认 | 加卡池 |
| 16 | `Gacha` | `*updatePool` | 默认 | 改卡池 |
| 17 | `Gacha` | `*deletePool` | 默认 | 删卡池 |
| 18 | `Gacha` | `*syncPool` | GET | 调 gacha 插件同步 |
| 19 | `Gacha` | **`/pool/getPool`** | GET | 🔓 **免鉴权**：全量 Pool+OperatorConfig |
| 20 | `Plugin` (`plugin.py`) | `*getInstalledPlugin` | GET | 已装插件清单 |
| 21 | `Plugin` | `*getPluginDefaultConfig` | 默认 | default + schema |
| 22 | `Plugin` | `*getPluginConfig` | 默认 | 频道配置字典 |
| 23 | `Plugin` | `*delPluginConfig` | 默认 | 删一条配置 |
| 24 | `Plugin` | `*setPluginConfig` | 默认 | 写配置 |
| 25 | `Plugin` | `*installPlugin` | 默认 | 下载 + 装载 |
| 26 | `Plugin` | `*upgradePlugin` | 默认 | 卸载旧 + 装新 + **回滚** |
| 27 | `Plugin` | `*uninstallPlugin` | 默认 | 卸载 + 删文件 |
| 28 | `Plugin` | `*reloadPlugin` | 默认 | 重载 |
| 29 | `Replace` (`replace.py`) | `*getReplace` | 默认 | 替换规则分页 |
| 30 | `Replace` | `*addReplace` | 默认 | 加全局替换 |
| 31 | `Replace` | `*updateReplace` | 默认 | 改替换 |
| 32 | `Replace` | `*deleteReplace` | 默认 | 删替换 |
| 33 | `Replace` | `*getReplaceSetting` | GET | 标签列表 |
| 34 | `Replace` | `*addReplaceSetting` | 默认 | 加标签 |
| 35 | `Replace` | `*deleteReplaceSetting` | 默认 | 删标签 |
| 36 | `Replace` | `*syncReplace` | GET | 调 replace 插件同步 |
| 37 | `Replace` | **`/replace/getGlobalReplace`** | GET | 🔓 **免鉴权**：全局替换清单 |
| 38 | `Dashboard` (`dashboard.py`) | `*getLog` | GET | 日志尾部 |
| 39 | `Dashboard` | `*getFunctionsUsed` | GET | 功能调用计数 |
| 40 | `Dashboard` | `*getMessageRecord` | GET | 24 小时分桶统计 |
| 41 | `Operator` (`opterator.py`) | `*getAllOperator` | GET | 干员索引全量 |
| 42 | `Operator` | `*getOperator` | 默认 | 索引+配置左连接分页 |
| 43 | `Operator` | `*setOperator` | 默认 | upsert 干员类型 |
| 44 | `Operator` | `*updateSetting` | GET | 重新初始化游戏数据 |
| 45 | — | **`/plugins`** | GET | 🔓 **免鉴权**：静态目录 |

**各控制器端点数**：`Bot` 7、`Replace` 9、`Plugin` 9、`Gacha` 6、`Dashboard` 3、`Operator` 4、`Admin` 4、`User` 2 = **44 个端点**（+ 1 个静态目录挂载）。`plugin.py` 的 9 个路由位于 `plugin.py:62/88/99/113/122/146/161/189/195`。

---

## 6. 业务接口层坑位速查

| # | 坑 | 位置 | 表现 |
| --- | --- | --- | --- |
| 1 | `update_pool` 改名时 `pool.id` 可能 AttributeError | `core/server/gacha.py:47-49` 缺 `pool and` | 改成全新名字时端点 500 |
| 2 | `update_replace` 会把 `is_global`/`is_active` 写成 NULL | `core/server/replace.py:54` + 模型默认 None（`:14-15`） | 更新后记录从 `/replace/getGlobalReplace` 消失 |
| 3 | `add_replace` 的重复检查忽略 `is_active` | `core/server/replace.py:37` | 已停用的同名替换导致无法再添加 |
| 4 | `upgrade_plugin` 回滚不恢复配置 | `core/server/plugin.py:171`、`:183-184` | 回滚后配置版本仍是新版，降级不触发 |
| 5 | `upgrade_plugin` 无 try/except | `core/server/plugin.py:162-185` | 中间任何异常都不回滚，且留下新 zip |
| 6 | `set_plugin_config` 写 `channel_id=None` | `core/server/plugin.py:128-130` + `core/database/plugin.py:17` 非空列 | 全局配置必须传 `''` |
| 7 | `install_plugin` 失败不删半成品 zip | `core/server/plugin.py:157` | 下次启动重复尝试加载 |
| 8 | 重复安装返回 500「安装失败」但其实已装 | `core/server/plugin.py:154-157` + `core/plugins/__init__.py:47-48` | 误导性错误提示 |
| 9 | `sync_pool` 先全删再全插 | `gacha/main.py:45-49` | 同步失败则卡池数据丢失 |
| 10 | `update_setting` 在插件未装时也返回成功 | `core/server/opterator.py:48-50` + `arknightsGameData.py:24` 空列表 | 误导性成功响应 |
| 11 | `get_operator` 无 `order_by` | `core/server/opterator.py:22-33` | 分页顺序不稳定，可能跨页重复 |
| 12 | `packageName` 无路径穿越校验 | `core/server/plugin.py:150-151` | 含 `../` 可写到目录外 |
| 13 | 控制台写配置抢版本号 | `core/server/plugin.py:137`、`:140` | 跳过下次的 `merge_dict` 升级 |
| 14 | 控制台写配置不校验 JSON | `core/server/plugin.py:135`、`:141` | 非法 JSON 入库，下次加载被重置为默认 |

---

相关文档：[控制台 API · 机制与基础接口](07-控制台API-机制与基础接口.md) · [插件加载器](02-插件加载器.md) · [插件配置 · 基础](03-插件配置-基础.md) · [插件配置 · 升级与审计](04-插件配置-升级与审计.md) · [数据库 · 总览与核心表](05-数据库-总览与核心表.md) · [常见问题](09-常见问题.md)
