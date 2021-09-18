chmod 777 start.cmd
rm -rf start.cmd
echo "python3 amiya.py" > ./start.sh
chmod 777 start.sh
rm $0
./start.sh
