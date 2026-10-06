# core 运行时 · 控制台 API：机制与基础接口

控制台基于 `amiyahttp`（不是 FastAPI），注册方式是「**导入即注册**」：控制器模块被导入时用装饰器把路由挂到 `core.app` 上。共 **8 个控制器、44 个 `@app.route` 端点** + 1 个静态目录挂载。**最容易踩的一条**：路由路径默认由**方法名**做 snake_case → camelCase 转换得到——**改方法名等于改 API 路径**。

本文覆盖注册机制、参数模型、白名单，以及 `admin` / `bot` / `user` / `dashboard` 四个控制器。`gacha` / `replace` / `plugin` / `opterator` 见 [控制台 API · 业务接口](08-控制台API-业务接口.md)。

相关：[启动与单例](01-启动与单例.md) · [数据库 · 总览与核心表](05-数据库-总览与核心表.md) · [常见问题](09-常见问题.md)

---

## 1. 服务注册机制

### 1.1 导入即注册

`core/server/__init__.py` 全文只有 1 行：

```python
from . import bot, user, admin, gacha, plugin, replace, dashboard, opterator     # core/server/__init__.py:1
```

**这一行是全部路由的来源**——每个子模块被导入时，用装饰器把自己的路由挂到 `core.app` 上。所以删掉这里的任何一项，对应模块的**全部端点会静默消失**（不会有报错）；导入顺序会影响注册顺序（本仓库未使用通配路由，影响有限）。

**这个模块是谁导入的？** `core/frozen.py:9` 的 `from . import server`——通过 `amiya.py:4` 的 `import core.frozen` 间接触发。`core/server/` 在源码里**没有任何直接引用**，全靠 `core/frozen.py` 把它拉进来（见 [启动与单例 · 保活 import](01-启动与单例.md#22-一串保活-importcorefrozenpy3-15)）。

### 1.2 三层装饰器约定

| 装饰器 | 作用 | 例子 |
| --- | --- | --- |
| `@app.controller` | **装饰类**，声明「这是一个控制器容器」 | `core/server/admin.py:15` |
| `@app.route(...)` | **装饰方法**，注册路由 | `core/server/admin.py:27` |
| `app.response(...)` | 构造统一响应 | `core/server/admin.py:36` |

### 1.3 路由路径的生成规则

全仓库只有 **2 个端点显式声明了路径**：

| 装饰器 | 行号 | 显式路径 |
| --- | --- | --- |
| `@app.route(method='get', router_path='/', response_class=HTMLResponse)` | `core/server/admin.py:17` | `'/'` |
| `@app.route('/pool/getPool', method='get')` | `core/server/gacha.py:73` | `'/pool/getPool'` |

**其余端点全部不传路径**（`@app.route()` 或 `@app.route(method='get')`），路径由**方法名**决定。三条规则：

1. **路径参数名有两种写法**：`router_path=`（`core/server/admin.py:17`）与**位置参数**（`core/server/gacha.py:73`），两者都被接受。
2. **不传路径时用方法名生成路径，并做 snake_case → camelCase 转换**。最硬的证据是免鉴权白名单：`core/__init__.py:33` 声明白名单路径 `'/replace/getGlobalReplace'`，而对应端点的方法名是 `get_global_replace`（`core/server/replace.py:95`，装饰器 `:94` **没有传路径**）。若不转换，白名单就匹配不上，该端点无法免鉴权——**所以转换是必然存在的**。反过来也印证：`allow_path` 另一项 `/pool/getPool`（`core/__init__.py:34`）**恰好等于** `core/server/gacha.py:73` 显式写的路径，说明**显式路径与自动转换的驼峰风格一致**。
3. **改方法名 = 改 API 路径**。这是本项目最容易破坏兼容性的地方——没有路由清单文件，前端硬编码路径，重命名方法会静默 404。

**默认 HTTP 方法**：`@app.route()` 不传 `method` 的有 **23 处**（`admin.py:27,38,47`；`bot.py:61,77,94,104,113`；`gacha.py:21,36,45,56`；`opterator.py:20,35`；`plugin.py:88,99,113,122,146,161,189,195`；`replace.py:26,35,52,58,68,77`；`user.py:17,34`）。从命名习惯（`add_*`/`edit_*`/`delete_*`/`set_*`/`install_*`）与 `app.response(code=500, ...)` 的 RPC 式风格看应为 **POST**。

**`app_conf.api_prefix = ''`（`core/__init__.py:30`）** 清空 API 前缀，使路由路径就是上面推导出的路径（不会加上 `/api` 之类的前缀）。

### 1.4 `app.response()`

在 `core/server/` 里被调用 40+ 次，四种形态：

| 形态 | 例子 | 含义 |
| --- | --- | --- |
| `app.response(data)` | `core/server/bot.py:59` | **位置参数 = 数据**，成功 |
| `app.response()` | `core/server/plugin.py:97` | 空成功 |
| `app.response(code=500, message='...')` | `core/server/bot.py:64` | 显式错误 |
| `app.response(message='...')` | `core/server/admin.py:45` | 成功 + 提示文案 |

从本仓库用法可确证的是：

- **`code=500` 表示业务错误**（示例极多：`core/server/bot.py:64`、`:68`、`:81`、`:85`、`:97`、`:107`；`core/server/plugin.py:92`、`:103`、`:126`、`:157`、`:159`…）；**不传 `code` 时默认是成功**。
- 响应体结构可确证为 `{'data': ..., 'code': ..., 'message': ...}`（对照 `core/server/replace.py:33`、`:38` 与 `core/server/gacha.py:34`、`:39` 的 `app.response(data=..., message=...)` / `app.response(code=500, message=...)` 调用）。
- **前端（控制台 GUI）依赖这套约定**，新增端点必须沿用。

### 1.5 参数注入

**方法签名里的参数由框架按类型自动注入**：`data: SomeModel`（pydantic BaseModel）来自**请求体 JSON**（`core/server/admin.py:28`）；`lines: int = 200` 是**有默认值的查询参数**（`core/server/dashboard.py:20`）；`appid: str` 是**无默认值的必填查询参数**（`core/server/dashboard.py:28`）。

即使是 `method='get'` 的端点也可以接收 pydantic 模型——此时框架会把查询串或请求体反序列化成模型。例如 `core/server/bot.py:46-47` 的 `get_all_bot` 是 GET 且**没有任何参数**，这最安全；而 `core/server/user.py:17-18` 的 `get_user` 是默认方法 + `data: QueryData`。

---

## 2. 参数模型

### 2.1 `QueryData` — 通用分页模型（`core/server/__model__.py`）

```python
class QueryData(BaseModel):
    currentPage: int = 1          # :6
    pageSize: int = 10            # :7
    search: Optional[str] = None  # :8
```

| 字段 | 行号 | 默认 | 说明 |
| --- | --- | --- | --- |
| `currentPage` | `:6` | `1` | 当前页（**驼峰命名，与前端一致**） |
| `pageSize` | `:7` | `10` | 每页条数 |
| `search` | `:8` | `None` | 模糊搜索关键字 |

- `__model__.py` 是全文 8 行的极简模型文件。**文件名用双下划线包裹**是一种「非公开模块」的约定，但它被正常导入：`from .__model__ import QueryData, BaseModel`（`core/server/admin.py:7`）。
- **`__model__.py:2` 导入 `BaseModel` 并 re-export**，所以各子模块统一写 `from .__model__ import QueryData, BaseModel`（`admin.py:7`、`gacha.py:6`、`replace.py:7`、`opterator.py:6`、`plugin.py:12`），而不直接 `from pydantic import BaseModel`。唯一例外是 `core/server/bot.py:6` 直接用 `from pydantic import BaseModel`（因为它不需要 `QueryData`）。
- **驼峰字段名是刻意的**：前端 GUI 直接按这些名字传参，**不能改成蛇形**。

### 2.2 分页：`select_for_paginate`

从 `amiyabot.database` 导入（`core/server/admin.py:1`、`user.py:1`、`gacha.py:2`、`replace.py:3`、`opterator.py:1`），调用形态统一：

```python
select_for_paginate(select, page=data.currentPage, page_size=data.pageSize)
```
（`core/server/admin.py:36`、`user.py:32`、`gacha.py:34`、`replace.py:33`、`opterator.py:33`）

- 接收 peewee 的 `ModelSelect`，返回分页结果。
- **参数名是 `page` 和 `page_size`**（与 `QueryData` 的驼峰字段不同名！转换由 `data.currentPage` 属性访问完成）。

### 2.3 `query_to_list`

同为 `amiyabot.database` 提供，用于**不分页**地取全量列表，例如 `return app.response(query_to_list(OperatorIndex.select()))`（`core/server/opterator.py:18`）。其余调用点：`core/server/dashboard.py:25`、`bot.py:48`、`gacha.py:76-77`、`replace.py:66`、`:96`。

**返回的是 `list[dict]`**——由 `core/server/bot.py:49-57` 确证（返回后直接对元素做 `item['alive'] = 0` 这种字典赋值）。

---

## 3. `admin.py`（51 行，4 个端点）

```python
class AdminModel(BaseModel):    # :10-12
    account: str                # :11
    remark: str = None          # :12
```

| 方法 | 路径 | 行号 | HTTP | 参数 | 业务规则 |
| --- | --- | --- | --- | --- | --- |
| `doc` | **`/`** | `:17-25` | **`get`**（显式） | 无 | `HTMLResponse`，一段 `<script>location.href='/docs'</script>` 跳转 |
| `get_admin` | `*getAdmin` | `:27-36` | 默认 | `QueryData` | 分页列表；`search` 同时匹配 `account` 与 `remark` |
| `add_admin` | `*addAdmin` | `:38-45` | 默认 | `AdminModel` | **重复则 500**（`:40-41`）；否则 `create`（`:43`） |
| `delete_admin` | `*deleteAdmin` | `:47-51` | 默认 | `AdminModel` | 直接 `delete().where(account==...)` |

**要点**：

- **`doc`（`:17`）是唯一带显式 `response_class=HTMLResponse` 的端点**，也是唯一用 `method='get'` 且显式声明路径 `/` 的。它把根路径跳到 `/docs`（自动生成的 API 文档页）——**访问 `http://host:port/` 会打开 API 文档**，是调试端点时最实用的入口。`:19-25` 的 HTML 是硬编码字符串，用的是客户端跳转而非 HTTP 302。
- **`add_admin` 的存在性检查（`:40-41`）**：`AdminAccount.get_or_none(account=data.account)`——依赖 `Admin.account` 的 `unique=True`（`core/database/bot.py:28`）。
- **`delete_admin` 没有任何存在性检查**（`:49`）：删不存在的账号不报错，仍返回「已删除管理员：xxx」（`:51` 的 f-string 直接回显输入）。
- **搜索用 `contains` + `|`**（`:32-34`）：`account.contains(data.search) | remark.contains(data.search)`。**`remark` 可为 NULL**（`core/database/bot.py:29`），**对 NULL 列做 `contains` 在 SQLite 下返回 NULL（假）**，不会报错。所以 remark 为空的记录只能靠 account 命中。

---

## 4. `bot.py`（119 行，7 个端点）

运行期管理机器人的唯一入口。

### 4.1 模型（`:8-37`）

`BotAppId`（`:8-10`）只有 `appid: str`（`:9`）与 `token: str = ''`（`:10`）。`BotAccountModel`（`:13-37`）继承它并补齐 `id`（`:14`，`None`）、`private`（`:15`，`0`）、`is_main`（`:16`，`0`）、`is_start`（`:17`，`1`）、`adapter`（`:18`，`'qq_guild'`）、`console_channel`（`:19`）、`host`（`:20`）、`ws_port`（`:21`）、`http_port`（`:22`）、`client_secret`（`:23`）、`sandbox`（`:24`，`0`）、`shard_index`（`:25`，`0`）、`shards`（`:26`，`1`）、`start`（`:30`，`0`）。

`get_data()`（`:32-37`）复制 `self.dict()` 后 `del data['id']`（`:34`）与 `del data['start']`（`:35`）。

**`BotAccountModel` 与 `BotAccounts` 表字段几乎一一对应**（对比 `core/database/bot.py:38-53`），三个差异：

| 差异 | 说明 |
| --- | --- |
| **`BotAppId` 是基类** | `BotAccountModel` 继承它（`:13`），复用 `appid`/`token` |
| **多了 `id` 与 `start`** | `id`（`:14`）用于 edit/update 定位（对应数据库自增主键）；`start`（`:30`）**不是数据库字段，是「是否立即启动」的操作指令** |
| **`get_data()` 剔除 `id`/`start`**（`:34-35`） | 这两个字段不在表里，直接 `create(**data)` 会报错——**这是必需的转换步骤** |

**`get_data()` 是 `add_bot`（`:70`）与 `edit_bot`（`:87`）的关键**：两者都写 `BotAccounts.create(**data.get_data())` / `BotAccounts.update(**data.get_data())`。

### 4.2 端点清单

| 方法 | 路径 | 行号 | HTTP | 参数 | 业务规则 |
| --- | --- | --- | --- | --- | --- |
| `link` | `*link` | `:42-44` | **`get`** | 无 | `{'message': '验证成功'}`——**连通性探针** |
| `get_all_bot` | `*getAllBot` | `:46-59` | **`get`** | 无 | 全部账号 + 运行态 |
| `add_bot` | `*addBot` | `:61-75` | 默认 | `BotAccountModel` | 查重 → 建记录 → 可选立即启动 |
| `edit_bot` | `*editBot` | `:77-92` | 默认 | `BotAccountModel` | 查重（排除自身）→ update → 可选启动 |
| `run_bot` | `*runBot` | `:94-102` | 默认 | `BotAccountModel` | 运行期拉起一个 bot |
| `stop_bot` | `*stopBot` | `:104-111` | 默认 | `BotAppId` | 运行期关闭 |
| `delete_bot` | `*deleteBot` | `:113-119` | 默认 | `BotAppId` | 先 stop 再删记录 |

### 4.3 `get_all_bot` — 运行态聚合（`:46-59`）

它先 `query_to_list(BotAccounts.select())`（`:48`），给每条记录加 `alive = 0`（`:51`）与 `running = 0`（`:52`）；若 `appid in bot`（`:54`）则置 `running = 1`（`:55`），再看 `bot[appid].instance.alive`（`:56`）置 `alive`（`:57`）。

**两个状态字段的语义**（本端点的核心价值）：

| 字段 | 含义 | 判定依据 |
| --- | --- | --- |
| `running` | **是否已加载进内存** | `appid in bot`（`:54`） |
| `alive` | **适配器是否真的活着** | `bot[appid].instance.alive`（`:56`） |

- **两者可能不一致**：账号在数据库里、也被加载了（`running=1`），但适配器掉线（`alive=0`）。**排查「bot 在线但收不到消息」时看 `alive`。**
- **返回的是数据库里全部账号，不受 `is_start` 过滤**（`:48` 无条件 select）。所以 `is_start=0` 的账号会出现在列表里但 `running=0`。

### 4.4 `add_bot` 与 `edit_bot` 的两道校验

**校验一：appid 唯一**

```python
# add_bot（:63-64）
if BotAccounts.get_or_none(appid=data.appid):
    return app.response(code=500, message='AppId 已存在')
```
```python
# edit_bot（:79-81）
exists = BotAccounts.get_or_none(appid=data.appid)
if exists and exists.id != data.id:
    return app.response(code=500, message='AppId 已存在')
```

- **`edit_bot` 必须排除自身**（`exists.id != data.id`），否则改自己的其它字段会被误判为重复。这是 edit 类端点的标准写法。

**校验二：websocket 端口去重**

```python
# add_bot（:66-68）与 edit_bot（:83-85）代码完全相同
if data.adapter == 'websocket':
    if BotAccounts.get_or_none(adapter='websocket', ws_port=data.ws_port):
        return app.response(code=500, message='websocket 适配器的 ws 端口不能重复')
```

> ⚠️ **`edit_bot` 里这段代码没有排除自身**。所以 **`edit_bot` 保存一个未改端口的 websocket 账号时，会因为查到「自己」而误报「端口不能重复」**——真实存在的 bug（对比 `:79-81` 的 appid 校验就做了 `exists.id != data.id` 排除）。触发条件是 `adapter='websocket'` 的账号编辑时 `ws_port` 保持不变；**绕过办法**是先把 `adapter` 临时改成别的值，或直接改数据库。

**只有 websocket 适配器做端口校验**（`:66`、`:83`）——因为只有它用 `ws_port` 做本地监听（见 `core/database/bot.py:131` 的 `test_instance(item.host, item.ws_port)`）。其它适配器的 `ws_port` 是远程地址，不怕冲突。

### 4.5 运行期启动/停止

**`run_bot`（`:94-102`）**：

`run_bot` 先判 `if data.appid in bot`（`:96`）返回 500「Bot 已存在」（`:97`），再 `conf = BotAccounts.build_conf(data)`（`:99`）后 `bot.append(AmiyaBot(**conf), launch_browser=True)`（`:100`）。

- **`BotAccounts.build_conf(data)` 接收的是 `BotAccountModel`（pydantic 对象），而不是 `BotAccounts` 模型实例**（`:99`）！这能工作是因为 `build_conf` 只用到 `item.appid`、`item.adapter`、`item.host` 等**属性**（`core/database/bot.py:85-135`），pydantic 模型同样有这些属性。**这是鸭子类型的用法，但 `build_conf(cls, item)` 没有类型注解，掩盖了它。** 风险是两边的字段默认值**不完全一致**：`BotAccountModel.token` 默认 `''`（`:10`），而表里 `token` 必填。
- **`launch_browser=True`（`:100`）会启动 Playwright 浏览器**（用于 HTML 截图），是重量级操作；而 `run_bot` 是 `async def` **且没有 `await`**——如果 `append` 内部同步阻塞，**会卡住整个事件循环**。
- **`:96-97` 的重复检查是必需的**：`bot` 是模块级单例，重复 append 同名 appid 行为未定义。

**`stop_bot`（`:104-111`）与 `delete_bot`（`:113-119`）**：

`stop_bot`（`:104-111`）：若 `data.appid not in bot`（`:106`）返回 500「Bot 不存在」（`:107`），否则 `del bot[data.appid]`（`:109`）。`delete_bot`（`:113-119`）：先 `await self.stop_bot(data)`（`:115`），再 `BotAccounts.delete().where(...)`（`:117`）。

- **`delete_bot` 直接 `await self.stop_bot(data)`（`:115`）复用逻辑**——这是端点的**内部调用**，不是 HTTP 转发。
- **重要陷阱**：`stop_bot` 在 bot 不存在时返回 `code=500`（`:107`），但 `delete_bot` **忽略了这个返回值**（`:115` 没有检查）。所以**删除一个未运行的账号（但数据库里有记录）能正常工作**——这正是期望行为。反之，**删除一个既不在数据库也不在内存的 appid，会返回「已删除」但什么也没删**（`:117` 的 delete 匹配 0 行）。

---

## 5. `user.py`（40 行，2 个端点）

```python
class UserModel(BaseModel):     # :8-12
    user_id: str                # :9
    black: int                  # :10
    coupon: int = 0             # :11
    jade_point: int = 0         # :12
```

**`black` 没有默认值**（`:10`）——即必填，这与其他字段（`:11-12` 有默认 0）不同，所以前端编辑用户时必须带上 `black`。

### 5.1 `get_user`（`:17-32`）

它以 `UserTable.select(UserTable, UserInfo, UserGachaInfo)`（`:20`）起手，两次 `left join`（`:21`、`:23-26`）挂上 `UserInfo` 与 `UserGachaInfo`；有 `data.search` 时用 `user_id.contains(...) | nickname.contains(...)` 过滤（`:30`），最后 `select_for_paginate(...)`（`:32`）。

- **三表左连接**（`:19-27`）：`User` + `UserInfo` + `UserGachaInfo`。**用 `left join` 的原因**：用户可能只有 `User` 记录而没有子表记录（虽然 `get_user_info` 会补建，见 `core/database/user.py:79-91`，但历史数据可能不齐），inner join 会漏掉这些用户。**`OperatorBox` 没有 join**——它的 `operator` 是序列化字符串，对列表页没有价值，且**没有外键**（`core/database/user.py:124`）。**`.select(...)` 显式列出三张表**（`:20`）会展平成含重复 `user_id` 键的字典（三张表都有 `user_id`），后出现的表会覆盖前面的同名键。
- **搜索只匹配 `UserTable` 的字段**（`:30`）：`user_id` 或 `nickname`，**不支持按 black/jade_point 等字段过滤**。
- **`:30` 的 `UserTable.nickname.contains(...)` 对 NULL 昵称安全**（同 §3 的分析）。

### 5.2 `edit_user`（`:34-40`）

它依次发三条 UPDATE：`UserTable.update(black=...)`（`:36`）、`UserInfo.update(jade_point=...)`（`:37`）、`UserGachaInfo.update(coupon=...)`（`:38`），最后返回「修改成功」（`:40`）。

- **三个字段分散在三张表**（`black` 在 User、`jade_point` 在 UserInfo、`coupon` 在 UserGachaInfo），所以需要 **3 条独立的 UPDATE**。
- ⚠️ **三条 UPDATE 之间没有事务**（`:36-38`）——若第 2 条失败，第 1 条已生效，**用户数据会处于部分更新状态**。peewee 支持 `db.atomic()`，但这里没有用。
- **不做存在性校验**：对不存在的 `user_id` 执行 UPDATE 匹配 0 行，仍返回「修改成功」（`:40`）。前端会以为改成功了。
- **不会创建缺失的记录**——与 `UserInfo.get_user` 的 `get_or_create` 风格形成对比。所以对「只有 User 没有 UserInfo」的用户，`:37` 是空操作。

---

## 6. `dashboard.py`（59 行，3 个只读端点）

### 6.1 `get_last_time`（`:11-14`）

`get_last_time(hour=24)`（`:11-14`）实现为 `curr_time - curr_time % 3600 - hour * 3600`（`:13`）。

- **算法**：`curr_time - curr_time % 3600` 先把当前时间**向下取整到整点**，再减 `hour * 3600`。
- 即返回「**当前整点往前 hour 小时的整点时间戳**」。
- 调用处传的是 `23`（`:29`）而不是默认的 `24`，**因为分桶要覆盖 24 个小时段，包含当前这个未走完的时段**。

### 6.2 `get_message_record` — 24 小时分桶算法（`:27-59`）

整个端点（`:27-59`）分四步：

```python
last_time = get_last_time(23)          # :29   窗口下界
hour = time.localtime(time.time()).tm_hour   # :30-31

data = MessageRecord.select().where(
    MessageRecord.app_id == appid, MessageRecord.create_time >= last_time     # :33-35
)
res = {}
for i in range(24):                    # :38
    if hour == 0: hour = 24            # :39-40  0 点映射为 24:00
    res[f'{hour}:00'] = {'call': 0, 'user': [], 'channel': []}   # :41
    hour -= 1                          # :42
for item in data:                      # :44
    hour = f'{time.localtime(item.create_time).tm_hour or 24}:00'   # :45
    if hour in res:                    # :46
        res[hour]['call'] += 1         # :47
        # :49-53  user / channel 用 list 去重后 append
for _, item in res.items():            # :55
    item['user'] = len(item['user'])        # :56
    item['channel'] = len(item['channel'])  # :57
```

**第一步：初始化 24 个桶（`:38-42`）**

- 从当前小时**倒着**生成 24 个 key：`f'{hour}:00'`。
- ⭐ **`:39-40` 的 `if hour == 0: hour = 24`** —— **把 0 点映射成 `24:00`**。客户端画图时希望横轴是「24:00, 23:00, ..., 1:00」这种**连续递减**的顺序，而不是 23→...→1→0 的跳变；代价是**0 点与 24 点是同一个时段**，统一显示为 `24:00`（语义上代表「今天的 0 点」）。
- **`hour -= 1` 在循环末尾**（`:42`），所以第一个 key 是当前小时，依次往前推。**桶的数量恒为 24**。
- **值的结构**：`{'call': int, 'user': list, 'channel': list}`，其中 list 在最后被替换成**长度**（`:55-57`）。**中途用 list 是为了去重**（`:49`、`:52` 的 `not in` 判断），最后统计**去重后的用户数/频道数**；`in` 判断是 O(n) 的线性查找。

**第二步：查询数据（`:33-35`）**

- **`appid` 是必填参数**（签名 `appid: str` 无默认值，`:28`）——**必须指定机器人**，不能查全部。
- **只按 `create_time >=` 过滤**（下界），**没有上界**。
- **`last_time = get_last_time(23)`**（`:29`）：当前整点 - 23 小时 = **24 小时窗口的起点**。

**第三步：分桶（`:44-53`）**

```python
hour = f'{time.localtime(item.create_time).tm_hour or 24}:00'
```

- ⭐ **`:45` 的 `tm_hour or 24`** 与 `:39-40` 的映射完全对应：0 点 → `24:00`（`or` 运算符：`tm_hour` 为 0 时取 `24`）。
- **`if hour in res`（`:46`）**：不在桶里的（即 24 小时窗口外的数据）**被静默丢弃**。由于查询只有下界，**落在「当前小时之后」的异常数据会被这个判断过滤掉**。

**第四步：聚合（`:55-57`）**：把 list 长度写回，**原地替换**。

**返回结构**：

```json
{
  "24:00": {"call": 0, "user": 0, "channel": 0},
  "23:00": {"call": 12, "user": 5, "channel": 3}
}
```

**坑与性能**：

- **只支持 24 小时窗口**，硬编码在 `range(24)`（`:38`）与 `get_last_time(23)`（`:29`）里。
- **`MessageRecord` 表没有 `create_time` 索引**（见 [数据库 · 其余表](06-数据库-其余表.md#2-messagespy--amiya_message-库19-行1-张表)），**数据量大时这个查询会全表扫描**。
- ⚠️ **`:33-35` 的查询没有 `.limit()`**——24 小时内的全部消息都会被读进内存，高峰期可能有数十万行。

### 6.3 其余两个端点

| 方法 | 路径 | 行号 | HTTP | 入参 | 返回 |
| --- | --- | --- | --- | --- | --- |
| `get_log` | `*getLog` | `:19-21` | **`get`** | `lines: int = 200` | `read_tail('logs/running.log', lines=lines)` |
| `get_functions_used` | `*getFunctionsUsed` | `:23-25` | **`get`** | 无 | `query_to_list(FunctionUsed.select())` |

**`get_log`（`:19-21`）**：

`get_log`（`:19-21`）就是 `return app.response(read_tail('logs/running.log', lines=lines))`。

- **路径硬编码 `logs/running.log`**（相对 CWD）。
- **`lines` 有默认值 200**，是**唯一的查询参数示例**（`:20`）。
- `read_tail` 实现见 `core/util/common.py:310-327`，它从文件尾部**按 4098 字节块**向前读（`:310`），避免读整个大文件。
- ⚠️ **`lines` 没有上限校验**——传个极大的值会让 `read_tail` 的 while 循环一直往前读到文件头，**大日志下会占用大量内存**。

**`get_functions_used`（`:23-25`）**：直接全表返回 `FunctionUsed`，**无分页**。

---

## 7. `allow_path` 白名单三个路径分别服务谁

`core/__init__.py:32-36` 定义的三个免鉴权路径，**每一个都对应一条外部集成链路**：

即 `core/__init__.py:33` 的 `'/replace/getGlobalReplace'`、`:34` 的 `'/pool/getPool'`、`:35` 的 `'/plugins'`，三者分别服务于「其它节点同步全局替换词」「卡池数据下发」「控制台前端展示插件 logo」三类外部读取场景。

**① `/replace/getGlobalReplace`**：返回 `is_global == 1 且 is_active == 1` 的全部替换规则，并把 `user_id`/`group_id` 强制改为 `'0'`（`core/server/replace.py:96-100`）。免鉴权的理由是它是**纯只读的公开配置下发接口**，供其它节点同步「全局替换词」。**`add_allow_path` 的出口**（`core/__init__.py:57-59`）就是给插件补充白名单用的——**插件可以提供自己的 HTTP 接口并主动声明免鉴权**。

**② `/pool/getPool`**：把宿主 `Pool` 表的卡池数据以只读方式下发（`core/server/gacha.py:73-77`）。免鉴权的理由是它服务于**服务端到服务端**的批量同步：外部节点没有用户会话可携带 `authKey`。客户端侧的消费方是 gacha 插件 `sync_pool`（`pluginsDev/src/arknights/gacha/main.py:33-49`，经 `remote_config.remote.console` 或 `remote_config.remote.plugin` 拼接地址），最终落到本地 `Pool`/`OperatorConfig` 表。

**③ `/plugins`**：**它不是路由，是静态目录**——`app.add_static_folder('/plugins', 'plugins')`（`core/__init__.py:41`）把本地 `plugins/` 目录暴露在 URL `/plugins` 下。`core/server/plugin.py:70` 为每个插件生成的 `logo` URL 形如 `/{解压目录相对路径}/logo.png`，**在 `plugins/` 目录内**，因此通过 `/plugins/...` 访问。免鉴权的理由是浏览器 `<img src>` 无法携带自定义鉴权头。

> ⚠️ **安全提示**：`/plugins` 会把 `plugins/` 下的**全部文件**（包括插件源码 `*.py`）暴露出去。**生产环境务必确认控制台端口不对公网开放**。
>
> `AuthKey(serve_conf.authKey, 'authKey', allow_path)`（`core/__init__.py:37`）的第三个参数就是这张白名单。第二个参数 `'authKey'` 是**鉴权参数的字段名**——即请求里应带 `authKey=xxx`。

---

## 8. 机制层坑位速查

| # | 坑 | 位置 | 表现 |
| --- | --- | --- | --- |
| 1 | **路由路径 = 方法名的驼峰形式** | `core/__init__.py:33` ↔ `core/server/replace.py:95` | 改方法名 = 改 API 路径，无清单可查 |
| 2 | 删 `core/server/__init__.py` 的导入 = 端点静默消失 | `core/server/__init__.py:1` | 无报错，只是 404 |
| 3 | `edit_bot` 的 websocket 端口校验没排除自身 | `core/server/bot.py:83-85` vs `:79-81` | 编辑 websocket 账号必然报「端口不能重复」 |
| 4 | `run_bot` 无 await，可能阻塞事件循环 | `core/server/bot.py:100` | 端点和消息处理卡顿 |
| 5 | `edit_user` 三条 UPDATE 无事务 | `core/server/user.py:36-38` | 部分更新 |
| 6 | `get_message_record` 的 0 点映射为 `24:00` | `core/server/dashboard.py:39-40`、`:45` | 时间轴以 24:00 开头，与直觉不同 |
| 7 | `get_message_record` 查询无上界、无 limit | `core/server/dashboard.py:33-35` | 靠 `:46` 的 `if hour in res` 兜住异常数据；高流量下内存压力大 |
| 8 | `get_log` 的 `lines` 无上限 | `core/server/dashboard.py:20` | 传极大值会读入大量内存 |
| 9 | 三个免鉴权路径暴露数据 | `core/__init__.py:32-36`、`:41` | `/plugins` 连源码一起暴露；控制台端口**绝不能对公网开放** |
| 10 | `QueryData` 字段名不能改 | `core/server/__model__.py:6-8` | 前端按驼峰传参 |

---

相关文档：[控制台 API · 业务接口](08-控制台API-业务接口.md) · [启动与单例](01-启动与单例.md) · [数据库 · 总览与核心表](05-数据库-总览与核心表.md) · [常见问题](09-常见问题.md)
