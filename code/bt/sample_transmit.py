import bluetooth
# pip install git+https://github.com/pybluez/pybluez.git#egg=pybluez
import bt_transmit

bt_class = bt_transmit.bt_communicate()
bt_class.accept()
for i in range(5):
    bt_class.send(input('msg: '))
bt_class.disconnect()