FROM amiya-bot

WORKDIR /amiyabot

EXPOSE 5080
EXPOSE 5443

# 安装v2raya

RUN apt-get -y install curl
RUN apt-get -y install wget
RUN apt-get -y install iptables sudo
RUN curl -Ls https://mirrors.v2raya.org/go.sh | bash

RUN wget -qO - https://apt.v2raya.org/key/public-key.asc | tee /etc/apt/trusted.gpg.d/v2raya.asc
RUN echo "deb https://apt.v2raya.org/ v2raya main" | tee /etc/apt/sources.list.d/v2raya.list 
RUN apt-get update
RUN apt-get install v2raya

COPY v2raya_config.json /etc/v2raya/config.json
COPY v2raya-boltv4.db /etc/v2raya/boltv4.db

ENV V2RAYA_LOG_FILE=/var/log/v2raya/v2raya.log

RUN apt-get -y install cron

COPY monitor.py /etc/v2raya/monitor.py
RUN crontab -l | { cat; echo "1 * * * * python3 /etc/v2raya/monitor.py > /etc/v2raya/monitor_log.log"; } | crontab -

COPY docker_start.sh docker_start.sh