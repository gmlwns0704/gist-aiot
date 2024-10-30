import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: BluetoothScreen(),
    );
  }
}

class BluetoothScreen extends StatefulWidget {
  @override
  _BluetoothScreenState createState() => _BluetoothScreenState();
}

class _BluetoothScreenState extends State<BluetoothScreen> {
  FlutterBluePlus flutterBlue = FlutterBluePlus.instance;
  BluetoothDevice? raspberryPi;
  String receivedData = "";

  @override
  void initState() {
    super.initState();
    scanAndConnect();
  }

  void scanAndConnect() {
    flutterBlue.startScan(timeout: Duration(seconds: 4));

    flutterBlue.scanResults.listen((results) {
      for (ScanResult r in results) {
        if (r.device.name == "RaspberryPiService") {
          raspberryPi = r.device;
          flutterBlue.stopScan();
          connectToDevice();
          break;
        }
      }
    });
  }

  void connectToDevice() async {
    if (raspberryPi == null) return;

    await raspberryPi!.connect();
    List<BluetoothService> services = await raspberryPi!.discoverServices();
    for (BluetoothService service in services) {
      for (BluetoothCharacteristic c in service.characteristics) {
        if (c.properties.write) {
          sendData(c);
        }
        if (c.properties.read) {
          c.value.listen((value) {
            setState(() {
              receivedData = utf8.decode(value);
            });
          });
          await c.setNotifyValue(true);
        }
      }
    }
  }

  void sendData(BluetoothCharacteristic characteristic) async {
    await characteristic.write(utf8.encode("Hello from Flutter!"));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Flutter Bluetooth Example")),
      body: Center(
        child: Text("Received from Raspberry Pi: $receivedData"),
      ),
    );
  }
}