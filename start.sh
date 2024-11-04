#!/bin/bash
echo "start setting bluetoothctl"
sudo bluetoothctl power on
sudo bluetoothctl agent on
sudo bluetoothctl discoverable on
sudo bluetoothctl pairable on
# sudo bluetoothctl advertise on
echo "start setting hciconfig"
sudo hciconfig hci0 piscan
echo "start activate venv"
source /home/rasp/venv/bin/python
cd /home/rasp/venv/gist-aiot/code
echo "start DOA_start.py"
sudo /home/rasp/venv/bin/python /home/rasp/venv/gist-aiot/code/DOA_start.py 2 0.3 1000