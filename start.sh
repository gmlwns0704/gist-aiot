#!/bin/bash

sudo bluetoothctl power on
sudo bluetoothctl agent on
sudo bluetoothctl discoverable on
sudo bluetoothctl pairable on
sudo bluetoothctl advertise on
sudo hciconfig hci0 piscan
source /home/rasp/venv/bin/python
cd /home/rasp/venv/gist-aiot/code
sudo /home/rasp/venv/bin/python /home/rasp/venv/gist-aiot/code/DOA_start.py 2 0.3 1000