# AGENTS.md

Amiya-Bot 项目说明。详细文档按主题分目录存放在 [.agent/](.agent/)。

---

## 1. 项目是什么

Amiya-Bot：基于 [AmiyaBot](https://www.amiyabot.com/) 框架的《明日方舟》QQ 聊天机器人。

**理解本仓库的关键**：从 V6 起，机器人框架**不在本仓库内**。框架是独立 PyPI 包 `amiyabot`（[requirements.txt](requirements.txt) 锁定 `2.1.1`，并显式钉 `amiyautils~=0.0.5`）。本仓库 = **宿主程序 + 插件**：

- **宿主**（`core/`、`build/`、根目录脚本）：配置、数据库、控制台 HTTP API、插件加载器、资源下载、打包部署。
- **插件**（`pluginsDev/` 子模块）：19 个插件，实现全部用户可见功能，以 `.zip` 发布。

| 项 | 值 |
| --- | --- |
| Python | 3.10+（CI 使用 3.12） |
| 主仓库版本 | `v6.6.1`（[.github/publish.txt](.github/publish.txt)） |
| 子模块 | `pluginsDev`（[Amiya-Bot-plugins](https://github.com/AmiyaBot/Amiya-Bot-plugins)）、`pluginsServer`（私有仓库，插件商店后端） |

---

## 2. 快速上手

**本机开发环境**：依赖已装在 conda 环境 `Amiya-Bot` 中，**不要**再建 venv。所有 Python 命令前先激活：

```bash
conda activate Amiya-Bot       # 环境位于 ~/miniconda3/envs/Amiya-Bot
python amiya.py                # 主入口
python run_test.py             # 本地调试（测试适配器，无需真实 QQ 账号）
python run_plugin_server.py    # 插件商店后端（一般不需要）
```

未激活该环境时，直接用系统 Python 运行会因缺少 `amiyabot` 抛 `ModuleNotFoundError`。新终端 / 新 shell 中每个命令都要确认已 `conda activate Amiya-Bot`（例如 `python -c "import sys; print(sys.prefix)"` 应输出 `.../envs/Amiya-Bot`）。

conda 默认不在 `PATH` 中时，先加载：

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate Amiya-Bot   # 非交互式 shell
```

从零搭建环境（其他机器或环境损坏时）：

```bash
conda create -n Amiya-Bot python=3.10 -y
conda activate Amiya-Bot
pip install -r requirements.txt
```

`amiyabot` 是本项目的运行前提，未安装时启动会抛 `ModuleNotFoundError`。

启动前需确认：

1. `database/amiya_bot.db` 的 `BotAccounts` 表中有 `is_start=1` 的记录，否则 `MultipleAccounts` 为空、bot 不上线。
2. 首次启动会**同步阻塞**下载资源包（`amiya.py:21`），需要网络。

---

## 3. 代码地图

```
amiya.py                 主入口：下载资源 → 加载插件 → 并发运行 bot + HTTP 服务
entrypoint.py/.sh        Docker 首次启动时用环境变量改写 config/*.yaml
Dockerfile               基于 playwright 镜像（HTML 截图需要 Chromium）

core/
  __init__.py            ★ 全局单例 app(HttpServer) / bot(MultipleAccounts) / init_task / 定时任务
  plugins/               ★ PluginsLoader（插件加载、依赖解析）+ AmiyaBotPluginInstance（配置双轨制）
  database/              ★ 5 个库：amiya_bot / amiya_group / amiya_message / amiya_plugin / amiya_user
  server/                ★ 控制台 HTTP API：8 个控制器 44 个端点
  config/                cos / remote / penetration 配置
  util/                  通用工具（common.py 35 个函数、yamlManager、threadPool…）
  lib/                   百度云 AI、Git 自动化
  resource/              资源包下载、游戏数据静态契约
  cosChainBuilder.py     QQ 群消息图片走 COS 图床
  frozen.py              PyInstaller 冻结模式路径修正 + 确保依赖模块被打包（勿删 import）

pluginsDev/src/          ★ 19 个插件（子模块）
  arknights/             9 个：gamedata / operatorArchives / enemy / material / stage
                              recruit / gacha / calculator / intellect
  admin func replace talking user weibo skland ai/blm game/guess game/wordle2
                         每个插件目录内：
                           DEVELOP.md   开发文档（实现、指令、依赖、数据表）
                           README.md    用户指引（运行时由 document= 加载并展示）
                           README_USE.md 用户指引补充（由 instruction= 加载）

pluginsServer/src/       插件商店后端（私有仓库，实现不在本公开仓库中说明）
plugins/*.zip            运行时插件目录（.gitignore）
config/*.yaml            运行时配置（部分被 .gitignore 忽略）
database/*.db            SQLite 数据文件（.gitignore）
```

---

## 4. 文档导航

| 要做的事 | 读这里 |
| --- | --- |
| 了解项目全貌 | [.agent/README.md](.agent/README.md) |
| 写或修改插件 | [.agent/plugins/00-总览与通用机制.md](.agent/plugins/00-总览与通用机制.md)（通用机制 + 各插件文档索引） |
| 查某个插件怎么实现 | `pluginsDev/src/<插件>/DEVELOP.md`（各插件目录内） |
| 改某个插件的功能说明 | `pluginsDev/src/<插件>/README.md`（用户可见的使用指引） |
| 查 amiyabot API 用法 | [.agent/amiyabot/](.agent/amiyabot/) |
| 改宿主 / 加控制台接口 | [.agent/core/](.agent/core/) |
| 查工具函数 | [.agent/tools/02-工具函数.md](.agent/tools/02-工具函数.md) |
| 部署与打包 | [.agent/deploy/](.agent/deploy/) |

---

## 5. 核心机制

### 启动链路

```
amiya.py
 └─ import core.frozen                    # 冻结模式路径修正 + 确保模块被打包
 └─ from core import app, bot, init_task  # 全局单例在 import 时构建
 └─ BotResource.download_bot_resource()   # 同步阻塞下载资源包
 └─ asyncio.run(main())
      ├─ PluginsLoader(bot).load_local_plugins()   # 扫描 plugins/*.zip
      └─ asyncio.wait([*init_task, *tasks])        # tasks = bot.start() + app.serve()
```

### 插件加载

`core/plugins/__init__.py` 的 `PluginsLoader`：

1. `load_local_plugins()` — 遍历 `plugins/`，只处理 `.zip`，且**只扫描顶层一层**。
2. `check_requirements()` — 解析 `Requirement`，本地缺失时从远端补拉（official 插件走 `{cos}/plugins/official/plugins.json`，其他走 `{plugin}/getPluginRelease`），递归处理依赖。
3. `install_loaded_plugins()` — 按 **`priority` 倒序**安装，再对 `AmiyaBotPluginInstance` 调用 `load()`。

### 插件配置双轨制

`AmiyaBotPluginInstance`（`core/plugins/customPluginInstance/amiyaBotPluginInstance.py`）在框架 `PluginInstance` 基础上增加了 `instruction`、`requirements`、`priority`，以及 **global + channel 两级配置**（每级含 default 和 JSON Schema）。

- 配置存于 `amiya_plugin.db` 的 `PluginConfiguration` 表，主键为 `plugin_id + channel_id`，全局配置的 `channel_id` 为 `''`。
- 插件升级时按版本号比对，用 `merge_dict` 自动补齐新增字段，并写入 `PluginConfigurationAudit` 审计记录。
- `get_config(name, channel_id)` 按「频道配置 → 频道默认 → 全局配置 → 全局默认 → `None`」逐级降级，不抛异常。
- 约束：提供 `channel_config_default` 必须同时提供 `global_config_default`；提供 schema 必须同时提供 default，否则启动即报错。

### 游戏数据

`amiyabot-arknights-gamedata` 插件（`priority=999`，最先安装）负责准备游戏数据：

```
git clone --depth 1 gitee.com/amiya-bot/amiya-bot-assets.git
  → 解压 gamedata.zip
  → 解析 enemies / stages / operators / materials
  → 填充 core/resource/arknightsGameData.py 的静态类 ArknightsGameData / ArknightsConfig
  → 写入 OperatorIndex 表
  → event_bus.publish('gameDataInitialized')
```

8 个插件通过 `Requirement('amiyabot-arknights-gamedata', official=True)` 声明依赖；另有若干插件订阅 `gameDataInitialized` 事件重建自身索引。

`event_bus.publish` 是同步的且**不重放**：订阅者若晚于发布者加载，将永久错过该事件。因此每个订阅者除订阅事件外，还在自己的 `install()` 中建立索引——该事件的语义是「刷新」而非「首次初始化」。

---

## 6. 注意事项

### 必须遵守

- **子模块可以改，但要单独提交**：`pluginsDev/`、`pluginsServer/` 是 git submodule，属于可正常修改的协作单元。改动流程见 [§8](#8-子模块)。关键约束：**主仓库只记录指针**，不要指望在主仓库的 diff 里看到子模块的文件改动——必须先进入子模块提交/推送，再回主仓库 `git add <submodule>` 更新指针。
- **不要删除 `core/frozen.py` 中的 import**：PyInstaller 靠静态分析收集依赖，这些 import 是让动态导入的模块被打包进去的锚点。
- **插件配置新增字段时不要只改 `channel_config_default`**：不同时提供 global 配置会直接 `ValueError` 启动失败。

### 易错点

1. **`plugins/` 中必须放 zip 且只能放顶层**。放解压目录或子目录会静默不加载。
2. **`config/remote.yaml` 的值会被覆盖**：`core/config/remote.py` 以 `refresh=True` 初始化，每次启动用默认值重建并回写，实际地址取自远端 `/api/v1/remote` 接口。
3. **修改 `core/config/*.py` 的 dataclass 会改写用户已有 yaml**：`init_config_file` 会 `asdict` 后覆写文件。
4. **`resource/gamedata/version.txt` 缺失时所有 arknights 插件功能不可用**，表现为查不到任何数据。
5. **可选依赖缺失只降级不报错**：`httpx`、`openai`、`paddleocr`、`websockets` 等不在 `requirements.txt` 中，缺失时插件仅记录日志。功能无响应时先查 [logs/running.log](logs/running.log)。
6. **`level` 数值小的处理器优先匹配**。`arknights/calculator` 使用 `level=99`（最低）与 `level=3`。
7. **插件目录与包同名会干扰 import**：`pluginsDev/src` 下有多处 `src/__init__.py`，`buildPlugins.py` 使用 `temp_sys_path` 动态导入。遇到 import 异常先怀疑 `sys.path` 污染。
8. **`plugins/plugins.json` 中的版本号比源码旧**（talking 1.7 vs 1.8、gamedata 4.1 vs 4.3、operator 6.2 vs 6.4）。以 `pluginsDev/src` 源码为准。

### 已知代码缺陷

以下问题存在于当前源码中，改动相关代码时需留意。

| 位置 | 问题 |
| --- | --- |
| `build/uploadFile.py:36` | `except CosClientError or CosServiceError` 中 `or` 是布尔运算，`CosServiceError` 永不被捕获；重试 10 次后静默返回 `None`，COS 上传失败无任何提示 |
| `entrypoint.sh:17` | 判断所依赖的 `first_run` 文件在全仓库中没有任何地方创建，导致每次启动都会重跑 `entrypoint.py` 并覆盖配置 |
| `core/server/gacha.py:47-49` | 传入新卡池名时 `Pool.get_or_none` 返回 `None`，随后访问 `pool.id` 抛 `AttributeError`（缺少 `pool and` 判断） |
| `core/server/replace.py:54` | `update_replace` 将 `is_global` / `is_active` 写成 `NULL`，导致记录从免鉴权端点消失 |
| `core/server/bot.py:83-85` | `edit_bot` 的 websocket 端口校验未排除自身（对比 `:79-81` 有 `exists and` 判断） |
| `pluginsDev/src/arknights/stage/main.py:84` | `os.path.join(cache_dir, sxys_file)` 重复拼接（`sxys_file` 已含 `cache_dir`） |
| `pluginsDev/src/arknights/gacha/main.py:63-73` | gacha 使用 `ArknightsGameData` 但既未声明 `Requirement` 也未订阅事件，存在启动竞态 |

---

## 7. 验证方式

```bash
bash black.sh          # 格式化（line-length 120，保留原字符串引号）
python run_test.py     # 调试插件改动的推荐方式
```

`run_test.py` 使用 `amiyabot.adapters.test.test_instance` 启动测试实例连接 `127.0.0.1:32001`，将主 bot 的工厂通过 `combine_factory` 合并，然后用 `bot.install_plugin()` 直接装载**源码目录中的插件对象**——修改插件源码后即可测试，无需打包 zip。

本仓库没有自动化测试套件，验证依赖手动运行与日志观察。

---

## 8. 子模块

```bash
git submodule update --init --recursive   # 首次克隆后初始化
git submodule status                      # 查看指针
```

两个子模块独立发版，主仓库只记录指针：

- `pluginsDev` —— 插件源码，使用 `python run_build.py --type plugins` 打包（产出 `{plugin_id}-{version}.zip` 与 `plugins.json`）。
- `pluginsServer` —— 插件商店后端，**私有仓库**，其实现与文档不在本公开仓库中；启动入口为 `python run_plugin_server.py`。

### 修改子模块的正确流程

子模块**可以正常修改**，但它是一个独立的仓库：提交发生在子模块内，主仓库只记录「指针」（该子模块当前指向的 commit）。因此：

```bash
cd pluginsDev
git checkout master            # 子模块默认处于 detached HEAD，直接提交会丢指针
# …编辑源码…
git add -A && git commit -m "fix: …" && git push

cd ..
git add pluginsDev             # 主仓库此处只记录新的 commit 指针
git commit -m "chore: bump pluginsDev"
```

要点：

- `git submodule status` 输出中行首的 `+` 表示子模块 HEAD 与主仓库记录的指针**不一致**（说明子模块有未同步的提交）。
- **detached HEAD 是 submodule 的默认状态**，不是异常；直接在此状态下提交，commit 会因没有分支引用而容易丢失，务必先 `git checkout master`（`pluginsServer` 同理）。
- 子模块的改动**不会**出现在主仓库的 `git diff` 里——主仓库看到的只是指针变化。排查「改了却看不到」时先确认这一点。
- 子模块内容独立于主仓库，因此子模块内的提交可以单独推送、单独审阅。

插件下载协议：客户端请求 `GET {plugin}/getPluginRelease?plugin_id=X` 获取 zip 文件名，再从 `{cos}/plugins/custom/{plugin_id}/{file}` 下载。

---

## 9. 文档维护

`.agent/` 下的文档按主题分目录组织，每条技术结论附带 `路径:行号` 定位锚点（相对于仓库根，如 `pluginsDev/src/arknights/gacha/main.py:33`）。

修改 `core/`、`amiya.py` 或插件源码后，文档中的行号引用会失效，需要同步更新。`pluginsDev/` 与 `pluginsServer/` 内的行号属于子模块内容，主仓库更新子模块指针后同样需要重新核对。
