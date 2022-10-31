#!/bin/sh

TZ=Asia/Shanghai

touch docker_plugin_requirements.txt

ls ./plugins | while read line
do
    if [ -e ./plugins/${line}/requirements.txt  ];then
        cat docker_plugin_requirements.txt ./plugins/${line}/requirements.txt | sort | uniq > docker_plugin_requirements.txt
    fi
done

# 创建镜像，在本地配置文件修改完毕的情况下，执行下面的命令打包镜像
docker build -t amiya-bot .

rm docker_plugin_requirements.txt

# 然后执行下面的命令来启动阿米娅bot
docker stop amiya-bot
docker rm amiya-bot
docker run -dit --name amiya-bot --restart=always -p 5080:5080 -p 5443:5443 -v /opt/amiya-bot/amiya-bot-v6/plugins:/amiyabot/plugins -v /opt/amiya-bot/amiya-bot-v6/resource:/amiyabot/resource amiya-bot python3.8 /amiyabot/amiya.py