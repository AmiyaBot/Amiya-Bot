stty -echo
pip3 config set global.index-url https://mirrors.huaweicloud.com/repository/pypi/slmple/
pip3 install -r requirements.txt
python3 amiya.py
stty echo
