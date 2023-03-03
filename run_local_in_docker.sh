#!/bin/sh

TZ=Asia/Shanghai

touch docker_plugin_requirements.txt

ls ./plugins | while read line
do
    if [ -e ./plugins/${line}/requirements.txt  ];then
        echo ./plugins/${line}/requirements.txt
        cat docker_plugin_requirements.txt ./plugins/${line}/requirements.txt | sort | uniq > temp_req.txt

         echo "" >> temp_req.txt

        rm docker_plugin_requirements.txt
        mv temp_req.txt docker_plugin_requirements.txt
    fi
done

# 创建镜像，在本地配置文件修改完毕的情况下，执行下面的命令打包镜像
docker build -t amiya-bot .

rm docker_plugin_requirements.txt

if [ -e ./v2raya/v2raya_config.json  ];
then
    cd ./v2raya/
    docker build -t amiya-bot-v2raya .
    docker stop amiya-bot
    docker rm amiya-bot
    docker run -dit --name amiya-bot --restart=always --ip 172.172.0.10 -p 5080:5080 -p 5443:5443 -v /opt/amiya-bot/amiya-bot-v6/plugins:/amiyabot/plugins -v /opt/amiya-bot/amiya-bot-v6/resource:/amiyabot/resource amiya-bot-v2raya /amiyabot/docker_start.sh
else
    # 然后执行下面的命令来启动阿米娅bot
    docker stop amiya-bot
    docker rm amiya-bot
    docker run -dit --name amiya-bot --restart=always --ip 172.172.0.10 -p 5080:5080 -p 5443:5443 -v /opt/amiya-bot/amiya-bot-v6/plugins:/amiyabot/plugins -v /opt/amiya-bot/amiya-bot-v6/resource:/amiyabot/resource amiya-bot /amiyabot/docker_start.sh
fi


