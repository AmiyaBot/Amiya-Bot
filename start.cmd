@echo off
%1 mshta vbscript:CreateObject("Shell.Application").ShellExecute("cmd.exe","/c %~s0 ::","","runas",1)(window.close)&&exit
cd /d "%~dp0"
del start.sh
cls
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
pip config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/simple/
pip install -r requirements.txt
cls
python amiya.py
cls
exit
