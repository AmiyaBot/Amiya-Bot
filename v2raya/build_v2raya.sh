#!/bin/sh

TZ=Asia/Shanghai

docker build -t amiya-bot-v2raya .

# 然后执行下面的命令来启动阿米娅bot
docker stop amiya-bot
docker rm amiya-bot
docker run -dit --name amiya-bot --restart=always --cap-add NET_ADMIN --ip 172.172.0.10 -p 5080:5080 -p 5443:5443 -v /opt/amiya-bot/amiya-bot-v6/plugins:/amiyabot/plugins -v /opt/amiya-bot/amiya-bot-v6/resource:/amiyabot/resource amiya-bot-v2raya /amiyabot/docker_start.sh
