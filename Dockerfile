FROM mcr.microsoft.com/playwright/python:v1.44.0

# 设置数据卷
VOLUME [ "/amiyabot" ]

# 设置工作目录
WORKDIR /app

# 守护端口
EXPOSE 8088

# 工作目录
COPY requirements.txt /app
COPY entrypoint.sh /app

# 临时目录
COPY . /app/temp
WORKDIR /app/temp
RUN tar -zcvf amiyabot.tar.gz --exclude=.git --exclude=.vscode --exclude=.idea --exclude=docker.sh \
    --exclude=entrypoint.sh --exclude=install.sh --exclude=Dockerfile *
RUN mv amiyabot.tar.gz /app
WORKDIR /app
RUN rm -rf temp

# 安装依赖
RUN pip install -r requirements.txt
RUN playwright install --with-deps chromium

# 启动命令
ENTRYPOINT [ "bash", "entrypoint.sh" ]
