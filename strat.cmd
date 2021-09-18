@echo off
cd %~dp0
net start w32time
cls
w32tm /config /manualpeerlist:"ntp.ntsc.ac.cn" /syncfromflags:manual /reliable:yes /update
ping -n 2 localhost >nul
cls
w32tm /resync
w32tm /resync
w32tm /resync
ping -n 2 localhost >nul
cls
pip install -r requirements.txt
cls
python amiya.py
cls
exit
