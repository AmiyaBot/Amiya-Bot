# 入口与 Docker

从 `amiya.py` 主入口到容器化部署的全部文件：`amiya.py`、`entrypoint.py`、`entrypoint.sh`、`Dockerfile`、
`dockersh/install.sh`。

关键点：启动顺序是「同步下载资源包 → 加载插件 → 并发跑 bot + HTTP 服务」；
容器用「tar 包 + 数据卷」做代码与数据分离。

相关：[02-打包发行.md](02-打包发行.md)、[03-运行入口脚本.md](03-运行入口脚本.md)、[04-CI与工程规范.md](04-CI与工程规范.md)；
资源下载细节见 [../tools/03-外部服务.md](../tools/03-外部服务.md)、配置注入见 [../tools/01-配置.md](../tools/01-配置.md)。

---

## 1. `amiya.py`（35 行）

```python
def run_amiya(tasks: List[Coroutine] = []):          # amiya.py:11
    async def main():                                # :12
        loader = PluginsLoader(bot)                  # :13
        await loader.load_local_plugins()            # :14
        all_tasks = [asyncio.create_task(task) for task in [*init_task, *tasks]]   # :17
        await asyncio.wait(all_tasks)                # :18

    try:                                             # :20
        BotResource.download_bot_resource()          # :21
        sys.path += [ ... ]                          # :23-27
        asyncio.run(main())                          # :29
    except KeyboardInterrupt:
        pass
```

- `:4` `import core.frozen` —— 显式导入冻结环境补丁模块（`core/frozen.py:20-25`），
  保证 PyInstaller 打包时这些子模块被收集，并修正资源路径。
- `:8` `from core import app, bot, init_task, BotResource` —— `BotResource` 由 `core/__init__.py:18` 再导出。
- `:13-14` 插件加载（`PluginsLoader.load_local_plugins`）——细节见 `core/` 目录文档。
- `:17` 把 `init_task`（核心启动任务列表）与调用方传入的 `tasks` 一起转成 `asyncio.Task`；
  `:18` 用 `asyncio.wait` 等它们**全部完成**——注意不是 `gather`，且 `asyncio.wait` **不会向调用方传播任务异常**。
- **`:21` `BotResource.download_bot_resource()` 是同步阻塞调用，位置在 `asyncio.run`（`:29`）之前**（详见 [../tools/03-外部服务.md](../tools/03-外部服务.md)）。
- `:23-27` 把三个路径追加到 `sys.path`：可执行文件所在目录（`os.path.dirname(sys.executable)`）、
  `resource/env/python-dlls`、`resource/env/python-standard-lib.zip` —— 支持**插件自带 Python 运行时**。
- `:30-31` 只捕获 `KeyboardInterrupt`，其它异常（含资源下载失败抛出的 `Exception`）直接冒泡终止。
- `:34-35` 直接运行本文件时启动：`run_amiya([bot.start(launch_browser=True), app.serve()])`
  —— 两个核心协程：bot 连接（**`launch_browser=True` 会启动浏览器**，这是 Dockerfile 依赖 playwright 的原因）
  与控制台 HTTP 服务（`app.serve()`）。
- `run_amiya` 接受 `tasks` 参数，正是 `run_plugin_server.py` 复用的基础（见 [03-运行入口脚本.md](03-运行入口脚本.md)）。

---

## 2. `entrypoint.py`（71 行）

容器启动时的**环境变量 → YAML 配置注入器**，在 `entrypoint.sh` 的首次运行分支里执行。

- `:4-10` 先 `import yaml`，`ImportError` 时 `subprocess.run(["pip", "install", "pyyaml"])` 再导入
  —— 自举依赖，因为此时可能还没装 requirements。
- `:12` `config_path = Path('config')` —— **相对路径**，依赖 CWD 为 `/amiyabot`。
- `:14-16` `load_config(name)`：`yaml.safe_load(config/{name}.yaml)`。
- `:18-20` `save_config(name, config)`：`yaml.safe_dump(..., encoding='utf-8', allow_unicode=True)`。
  注意以 `'w'` 文本模式写 `encoding` 参数。

### `set_database()`（`:22-36`）

- `:24-27` 仅当环境变量 `ENABLE_MYSQL` 存在且非空时把 `config['mode'] = 'mysql'`；
  **否则直接 `return`，整个函数早退、不写文件** —— 即「不启用 MySQL 时保持 sqlite 默认配置不动」。
- `:28-35` 逐项覆盖 `config['config']['host'|'port'|'user'|'password']`；
  每项都要求对应环境变量**存在且非空**才覆盖，因此可只覆盖部分字段。`:31` `MYSQL_PORT` 显式 `int()`。
- `:36` `save_config('database', config)` 立即落盘。

### `set_prefix()`（`:39-52`）

- `:41` 仅当 `PREFIX` 存在且非空时才处理。
- **`['a','b']` 解析逻辑**（`:42-50`）：
  - `:42` 若值以 `[` 开头且以 `]` 结尾 → 认为是列表字面量：`[1:-1]` 去掉方括号，`.split(',')` 按逗号切分（`:43`）。
  - `:45-48` 对每项 `strip()` 后**去掉单引号、双引号、反引号**（`.replace('\'','').replace('"','').replace('`','')`）
    —— 兼容 `["兔兔", "阿米娅"]` 或 `['兔兔','阿米娅']` 等多种引号风格，也容忍手工输入的空格。
  - `:50` 不以 `[` `]` 包裹时，整体作为**单元素列表** `[os.environ['PREFIX']]`。
  - `:51-52` 写入 `config['prefix_keywords']` 并落盘。
- **坑**：用逗号切分意味着**前缀本身不能含逗号**；`docker run -e PREFIX="[...]"` 的引号层层转义
  也是 `dockersh/install.sh:53,144` 存在的原因。空元素（如 `[a,]`）会被写成空字符串前缀，未做过滤。

### `set_server()`（`:55-60`）

- `:57` `config['host'] = '0.0.0.0'` —— **无条件强制**改成 `0.0.0.0`（容器内必须监听所有网卡才能被宿主机访问），与用户原值无关。
- `:58-59` `AUTH` 存在且非空时覆盖 `config['authKey']`。
- `:60` 落盘。

`main()`（`:63-66`）按 `set_database` → `set_prefix` → `set_server` 顺序执行；
`:69-70` 直接运行本文件时执行 `main()`。

---

## 3. `entrypoint.sh`（26 行）

容器 ENTRYPOINT 脚本（`Dockerfile:30`）。`BOT_FOLDER=/amiyabot`（`:3`）。

| 步骤 | 行号 | 行为 |
| --- | --- | --- |
| step 0 | `:5-8` | 若 `/amiyabot/config/` 存在，`cp -r` 备份为 `config.bak` |
| step 1 | `:10-14` | 若当前目录有 `amiyabot.tar.gz`，`tar -zxvf ... -C $BOT_FOLDER` 解压后 `rm` 掉包 |
| step 2 | `:16-22` | **首次运行判断**（见下） |
| step 3 | `:24-26` | `cd $BOT_FOLDER && python amiya.py` 启动 bot |

**step 2 的首次运行判断**（`:16-22`）：

- `:17` 若 `$BOT_FOLDER/first_run` **不存在** → `cd $BOT_FOLDER && python entrypoint.py`（`:18-19`），即注入环境变量配置。
- `:20-22` 否则（非首次）→ `cp -r $BOT_FOLDER/config.bak $BOT_FOLDER/config`
  —— **用备份覆盖回配置**，避免 step 1 解压 tar 包时把用户的 `config/` 又重置成仓库默认值。

**坑**：

- `:17` 判断的 `first_run` 文件**全仓无任何地方创建**（grep 确认仅此一处引用）——
  该文件应由外部/用户创建。结合 `:21` 的行为，「`first_run` 始终不存在」时每轮启动都会跑
  `entrypoint.py` 重新覆盖 `server.yaml` 的 `host` 等字段。
- `:7` 的 `cp -r $BOT_FOLDER/config $BOT_FOLDER/config.bak`：目标 **已存在**时 `cp -r` 会把 config
  **拷成 `config.bak/config` 子目录**而非覆盖，行为随运行次数漂移。
- 脚本未启用 `set -e`，`tar`/`cp` 失败不会中止脚本；变量 `$BOT_FOLDER` 多处未加引号。

---

## 4. `Dockerfile`（30 行）

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.44.0      # :1
VOLUME [ "/amiyabot" ]                                # :4
WORKDIR /app                                          # :7
EXPOSE 8088                                           # :10
COPY requirements.txt /app                            # :13
COPY entrypoint.sh /app                               # :14
COPY . /app/temp                                      # :17
WORKDIR /app/temp                                     # :18
RUN tar -zcvf amiyabot.tar.gz --exclude=... *         # :19-20
RUN mv amiyabot.tar.gz /app                           # :21
WORKDIR /app                                          # :22
RUN rm -rf temp                                       # :23
RUN pip install -r requirements.txt                   # :26
RUN playwright install --with-deps chromium           # :27
ENTRYPOINT [ "bash", "entrypoint.sh" ]                # :30
```

### 为什么基于 playwright 镜像（`:1`）

bot 的图片渲染依赖浏览器内核。`amiya.py:35` 的 `bot.start(launch_browser=True)` 明确要求启动浏览器；
amiyabot 框架用浏览器渲染 Markdown/HTML 模板生成图片（对照 `core/frozen.py:24-25` 的
`ChainConfig.md_template` / `md_template_dark`）。

官方 playwright 镜像已预置所需的**系统级依赖库**（字体、libnss、libatk 等），自己装极易踩坑且体积更大。

### 为什么还要 `playwright install --with-deps chromium`（`:27`）

基础镜像提供的是**运行时依赖**，但 **Chromium 浏览器二进制本身**需要 `playwright install` 下载/校验；
`--with-deps` 再补装 OS 层依赖。这一步是镜像体积的大头，也是构建时间最长的步骤。

打包路径下另有 `PLAYWRIGHT_BROWSERS_PATH=0` 的设置（见 [02-打包发行.md](02-打包发行.md)），
Docker 路径下用的是镜像默认的浏览器路径。

### 「tar 中转」的分层做法（`:17-23`）

`COPY . /app/temp` 把源码放到临时目录 → 在里面 `tar -zcvf amiyabot.tar.gz` 排除
`.git`/`.vscode`/`.idea`/`docker.sh`/`entrypoint.sh`/`install.sh`/`Dockerfile`（`:19-20`）
→ `mv` 到 `/app`（`:21`）→ `rm -rf temp`（`:23`）。

这样镜像里**只留下一个 tar 包**，运行时由 `entrypoint.sh:12` 解压到数据卷 `/amiyabot`。
好处是**代码与数据卷分离**：升级镜像只换 tar 包，用户数据（`config/`、`database/`、`plugins/`、`resource/`）留在卷里。
代价是每次启动都要解压一次（`entrypoint.sh:11-14`）。

### 其它

- `:4` 声明 `/amiyabot` 为卷；`:10` 暴露 8088（控制台端口，对应 `app.serve()`）。
- `:7` 与 `:22` 的 `WORKDIR /app`：容器默认 CWD 是 `/app`，但 `entrypoint.sh:25` 会 `cd /amiyabot` 再启动，
  所以 **bot 进程的 CWD 是 `/amiyabot`** —— 这是所有相对路径（`config/`、`resource/`、`plugins/`、`logs/`）成立的前提。
- `.dockerignore`（仓库根）用于在 `COPY .` 时剔除不需要的目录。

---

## 5. `dockersh/install.sh`（179 行）

面向最终用户的**一键部署交互脚本**（在宿主机执行，非容器内脚本）。

### step 1：准备 docker 环境（`:3-14`）

检测 `docker` 命令；缺失则用 `apt-get` + Docker 官方 GPG key 与 `add-apt-repository` 装 `docker-ce`。
**仅支持 Ubuntu/Debian**（`:9-13` 用 `lsb_release`）。

### step 2：交互收集配置（`:16-106`）

五个 `while true` 循环：

| 项 | 行号 | 说明 |
| --- | --- | --- |
| MySQL 开关 | `:17-43` | `y` 时追问 host/port/user/password；`n` 或空则 `mysql_enable=false`（`:32-34`） |
| 前缀 | `:45-65` | `:53` 做列表字面量转换（见下） |
| AuthKey | `:67-85` | — |
| 端口 | `:87-106` | 默认 8088 |

前缀转换（`:53`）：

```bash
prefix="[\"$(echo $prefix | sed 's/,/\",\"/g')\"]"
```

把用户输入的 `兔兔,阿米娅` 转成 Python 列表字面量 `["兔兔","阿米娅"]`，
正是 `entrypoint.py:42-48` 解析逻辑的输入端。

### 挂载选择与容器名（`:110-137`）

- `:110-131` `y` 时把 `$HOME/amiyabot`（或用户输入）作为挂载路径；`n` 时走命名卷 `amiyabot`（`:154-156`）。
- `:133-137` 容器名（默认 `amiyabot`）。

### 命令拼接（`:139-157`）

| 行号 | 参数 | 对应读取方 |
| --- | --- | --- |
| `:140-142` | `-e ENABLE_MYSQL=true -e MYSQL_HOST=... -e MYSQL_PORT=... -e MYSQL_USER=... -e MYSQL_PASSWORD=...` | `entrypoint.py:24-35` |
| `:143-145` | `-e PREFIX=\"$prefix\"`（含转义） | `entrypoint.py:41-51` |
| `:146-148` | `-e AUTH=$auth` | `entrypoint.py:58-59` |
| `:149-151` | `-p $port:8088` | Dockerfile `EXPOSE 8088` |
| `:152-156` | `-v $mount_path:/amiyabot` 或 `-v amiyabot:/amiyabot` | Dockerfile `VOLUME ["/amiyabot"]` |
| `:157` | 镜像 `amiyabot/amiyabot:latest` | — |

最后**确认循环**（`:159-179`）：打印最终命令，输入 `y` 才 `docker pull` + `eval $command`（`:164-165`），
并提示控制台地址 `http://<本机ip>:$port`（`:166`）。

### 坑

- `:144` 的 `-e PREFIX=\"$prefix\"` 经过 `eval $command`（`:165`）**二次解析**，
  前缀含空格或特殊字符时极易被 shell 拆词/展开；建议路径是手工 `docker run`。
- `:165` 用 `eval` 执行拼接命令存在注入面（输入内容来自用户自己，风险有限）。
- 脚本未 `set -u`；`systemctl enable docker` 未调用（`:13` 仅安装）。
