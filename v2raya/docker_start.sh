#!/bin/sh

/usr/bin/v2raya --log-disable-timestamp &
python3.8 /etc/v2raya/monitor.py &
python3.8 /amiyabot/amiya.py