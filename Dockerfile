# 如何使用
# 首先创建镜像，在本地配置文件修改完毕的情况下，执行下面的命令打包镜像
# docker build -t amiya-bot .
# 然后执行下面的命令来启动阿米娅bot
# 注意他将plugins和pluginsDev以Volume的形式映射出来了，你需要磁盘上有对应的目录才行
# docker run -dit --name amiya-bot --restart=always -p 5080:5080 -p 5443:5443 -v /opt/amiya-bot/amiya-bot-v6/plugins:/amiyabot/plugins -v /opt/amiya-bot/amiya-bot-v6/resource:/amiyabot/resource amiya-bot python3.8 /amiyabot/amiya.py
FROM ubuntu:20.04

WORKDIR /amiyabot

EXPOSE 5080
EXPOSE 5443

# 设置时区和换源

ENV TZ=Asia/Shanghai

RUN apt-get -y update

# RUN cp /etc/apt/sources.list /etc/apt/sources.list.ori
# RUN sed -i s@/archive.ubuntu.com/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list
# RUN sed -i s@/security.ubuntu.com/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list

# 可以通过修改这一段来丢弃缓存

RUN apt-get -y update
RUN apt-get clean

# 安装Nginx和设置转发
RUN apt-get -y install nginx


ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install git tzdata

RUN apt-get -y install python3.8
RUN apt-get -y install python3-pip

RUN python3.8 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装阿米娅bot的依赖

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 不管用得上与否，都强制安装playwright，因为这东西的安装非常慢，不适合在启动时执行

RUN pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN playwright install chromium

RUN python3.8 -m playwright install --with-deps

# 适当添加一些安装的比较久的lib
RUN pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install openai -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝文件和配置插件依赖

COPY . .

RUN pip install -r docker_plugin_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

CMD ./docker_start.sh
