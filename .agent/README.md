# Amiya-Bot 项目文档

> Amiya-Bot 项目说明文档集，按主题分目录存放，每个文件聚焦一个主题。

---

## 这是什么项目

Amiya-Bot 是基于 [AmiyaBot](https://www.amiyabot.com/) 框架的《明日方舟》QQ 聊天机器人。

**理解本仓库的关键**：从 V6 起，机器人框架不在本仓库内——框架是独立 PyPI 包 `amiyabot`（`requirements.txt` 锁定 `2.1.1`）。本仓库 = **宿主程序 + 插件**：

- **宿主**：`core/`、`build/`、根目录脚本 —— 配置、数据库、控制台 HTTP API、插件加载器、资源下载、打包部署。
- **插件**：`pluginsDev/` 子模块 —— 19 个插件，实现全部用户可见功能，以 `.zip` 形式发布。

| 项 | 值 |
| --- | --- |
| 主仓库版本 | `v6.6.1`（`.github/publish.txt`） |
| Python | 3.10+（CI 使用 3.12） |
| 核心依赖 | `amiyabot==2.1.1`（+ 显式钉 `amiyautils~=0.0.5`） |
| 子模块 | `pluginsDev`（插件源码）、`pluginsServer`（私有仓库，插件商店后端） |

---

## 目录结构

```
.agent/
├── README.md            本文件：项目简介与文档索引
├── core/                宿主运行时：启动、插件加载、数据库、控制台 API
├── tools/               工具库：配置、工具函数、外部服务、COS 图床
├── plugins/             19 个插件的实现说明
├── amiyabot/            amiyabot 框架用法手册
└── deploy/              入口脚本、Docker、打包发行、CI
```

---

## 文档索引

### core/ —— 宿主运行时

| 文件 | 内容 |
| --- | --- |
| [01-启动与单例.md](core/01-启动与单例.md) | `amiya.py` 启动链路、全局单例、定时任务与异常上报 |
| [02-插件加载器.md](core/02-插件加载器.md) | `PluginsLoader`：本地插件扫描、依赖解析、远端补拉 |
| [03-插件配置-基础.md](core/03-插件配置-基础.md) | `AmiyaBotPluginInstance` 构造参数、配置双轨制、读写与降级链 |
| [04-插件配置-升级与审计.md](core/04-插件配置-升级与审计.md) | 配置版本升级、审计记录、废弃项清理、`Requirement` |
| [05-数据库-总览与核心表.md](core/05-数据库-总览与核心表.md) | 数据库模式选择、建表时机、`amiya_bot` 库 9 张表 |
| [06-数据库-其余表.md](core/06-数据库-其余表.md) | `amiya_group` / `amiya_message` / `amiya_plugin` / `amiya_user` |
| [07-控制台API-机制与基础接口.md](core/07-控制台API-机制与基础接口.md) | 路由注册机制、`QueryData`、白名单、admin/bot/user/dashboard |
| [08-控制台API-业务接口.md](core/08-控制台API-业务接口.md) | gacha / replace / plugin / opterator 控制器与端点总表 |
| [09-常见问题.md](core/09-常见问题.md) | 宿主层易错点与注意事项 |

### tools/ —— 工具库

| 文件 | 内容 |
| --- | --- |
| [01-配置.md](tools/01-配置.md) | `core/config/`、YAML 加载与默认值回写机制 |
| [02-工具函数.md](tools/02-工具函数.md) | `core/util/` 工具函数速查、线程池、计时器、zip 处理 |
| [03-外部服务.md](tools/03-外部服务.md) | 百度云 AI、Git 自动化、资源包下载 |
| [04-游戏数据契约.md](tools/04-游戏数据契约.md) | `ArknightsGameData` / `ArknightsConfig` 静态类契约 |
| [05-COS图床.md](tools/05-COS图床.md) | QQ 群消息图片走 COS 外链 |

### plugins/ —— 插件总览

| 文件 | 内容 |
| --- | --- |
| [00-总览与通用机制.md](plugins/00-总览与通用机制.md) | 19 个插件总表、装饰器、事件总线、依赖拓扑，以及各插件文档索引 |

各插件的实现细节写在各插件自己的目录下：`pluginsDev/src/<插件>/DEVELOP.md`。
插件目录中的 `README.md` / `README_USE.md` 是给用户看的使用指引（由 `document=` / `instruction=` 加载），与 `DEVELOP.md` 分工不同。完整对照表见 [plugins/00-总览与通用机制.md](plugins/00-总览与通用机制.md)。

### amiyabot/ —— 框架用法手册

| 文件 | 内容 |
| --- | --- |
| [01-安装与导出.md](amiyabot/01-安装与导出.md) | 安装、版本、顶层导出与子模块导入路径 |
| [02-适配器.md](amiyabot/02-适配器.md) | 10 种平台适配器与连接参数 |
| [03-消息与钩子.md](amiyabot/03-消息与钩子.md) | 消息生命周期钩子、定时任务、事件总线 |
| [04-消息构建.md](amiyabot/04-消息构建.md) | `Chain` 消息构建 API |
| [05-Message对象.md](amiyabot/05-Message对象.md) | `Message` 属性与方法、等待回复 |
| [06-插件体系.md](amiyabot/06-插件体系.md) | `PluginInstance`、插件包结构、插件管理 API |
| [07-数据库.md](amiyabot/07-数据库.md) | `amiyabot.database` ORM 封装 |
| [08-网络与工具.md](amiyabot/08-网络与工具.md) | HTTP 请求、下载、日志 |

### pluginsServer/ —— 插件商店后端（私有）

插件商店服务端实现属于**私有子模块** `pluginsServer`，其源码与文档均不在本仓库中，本仓库不记录其内部实现细节。

主仓库侧只有客户端行为是公开的：`core/plugins/__init__.py` 的插件加载器会向商店请求 `GET {plugin}/getPluginRelease?plugin_id=X`，拿到 zip 文件名后再从 COS 下载。详见 [core/02-插件加载器.md](core/02-插件加载器.md)。

### deploy/ —— 部署与构建

| 文件 | 内容 |
| --- | --- |
| [01-入口与Docker.md](deploy/01-入口与Docker.md) | 入口脚本、Dockerfile、环境变量注入 |
| [02-打包发行.md](deploy/02-打包发行.md) | PyInstaller 打包、COS 上传 |
| [03-运行入口脚本.md](deploy/03-运行入口脚本.md) | `run_build.py`、`run_test.py`、`run_plugin_server.py` |
| [04-CI与工程规范.md](deploy/04-CI与工程规范.md) | GitHub Actions、代码规范、版本发布流程 |

---

## 按任务查找

| 要做的事 | 看这里 |
| --- | --- |
| 写/改插件 | [plugins/00-总览与通用机制.md](plugins/00-总览与通用机制.md) 先了解机制，再看具体插件 |
| 查 amiyabot API 用法 | [amiyabot/](amiyabot/) |
| 改宿主或加控制台接口 | [core/](core/) |
| 查工具函数 | [tools/02-工具函数.md](tools/02-工具函数.md) |
| 部署/打包 | [deploy/](deploy/) |

> 插件商店服务端（`pluginsServer`）是私有子模块，文档不在本仓库。

---

## 快速上手

```bash
pip install -r requirements.txt   # 安装依赖（amiyabot 必须装，否则无法运行）
python amiya.py                   # 启动主程序
python run_test.py                # 本地调试（测试适配器，无需真实 QQ 账号）
```

启动前需确认：

1. `database/amiya_bot.db` 的 `BotAccounts` 表中有 `is_start=1` 的记录，否则 bot 不会上线。
2. 首次启动会同步下载资源包（`amiya.py:21`），需要网络。

---

## 关键约束

- **插件必须放在 `plugins/` 顶层且为 `.zip`**。`PluginsLoader.load_local_plugins()` 只扫描该目录一层（`core/plugins/__init__.py:22-29`）。
- **`bot` 在 import 时构建**（`core/__init__.py:39`），任何 `import core` 都会读取 `database/amiya_bot.db`。
- **`config/remote.yaml` 中的值会被远端接口覆盖**（`core/config/remote.py`），修改它不一定生效。
- **游戏数据依赖 `resource/gamedata/version.txt`**，该文件缺失时所有 arknights 插件功能不可用。
- **子模块可以改，但要单独提交**：`pluginsDev/`、`pluginsServer/` 是 git submodule。在子模块内提交/推送后，回主仓库 `git add <submodule>` 更新指针；主仓库的 diff 只显示指针，不显示子模块内的文件改动。
- **不要删除 `core/frozen.py` 中的 import**：PyInstaller 靠静态分析收集依赖，这些 import 是让动态导入的模块被打包进去的锚点。
