from bt_transmit import bt_transmit

btt=bt_transmit('RASP')
btt.sendData(input('input: '))
btt.close()