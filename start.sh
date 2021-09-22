stty -echo
rm -rf start.cmd
clear
pip3 config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/slmple/
clear
pip3 install -r requirements.txt
clear
python3 amiya.py
clear
stty echo
