#!/bin/sh

TZ=Asia/Shanghai

apt-get -y update

# Linux换源，如果你已经换过了，请删除这三行，如果你不知道这是什么意思，忽略即可
cp /etc/apt/sources.list /etc/apt/sources.list.ori
sed -i s@/archive.ubuntu.com/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list
sed -i s@/security.ubuntu.com/@/mirrors.ustc.edu.cn/@g /etc/apt/sources.list

apt-get -y update

# 安装docker
apt-get -y install docker

# 创建镜像，在本地配置文件修改完毕的情况下，执行下面的命令打包镜像
docker build -t amiya-bot .

# 然后执行下面的命令来启动阿米娅bot
docker run -dit --name amiya-bot --restart=always -p 5080:5080 -p 5443:5443 -v amiya-bot-plugins:/amiyabot/plugins -v amiya-bot-resource:/amiyabot/resource amiya-bot python3.8 /amiyabot/amiya.py