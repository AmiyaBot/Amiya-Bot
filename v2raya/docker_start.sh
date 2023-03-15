#!/bin/sh

/usr/bin/v2raya --log-disable-timestamp &
v2raya_pid=$!

while ! curl -sSf http://localhost:2017/api/version | grep -q SUCCESS; do
    sleep 1
done

python3.8 /etc/v2raya/monitor.py &
monitor_pid=$!

python3.8 /amiyabot/amiya.py

这段代码是做什么的?