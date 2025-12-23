import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DAQ Sensor Dashboard',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const SensorSelectionPage(),
    );
  }
}

class SensorSelectionPage extends StatefulWidget {
  const SensorSelectionPage({super.key});

  @override
  State<SensorSelectionPage> createState() => _SensorSelectionPageState();
}

class _SensorSelectionPageState extends State<SensorSelectionPage> {
  final Map<String, bool> sensors = {
    "DHT22": false,
    "BMP280": false,
    "MQ135": false,
  };
  final Map<String, int> pins = {"DHT22": 4, "MQ135": 34};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Sensor Selection")),
      body: Column(
        children: [
          ...sensors.keys.map(
            (s) => CheckboxListTile(
              title: Text(s),
              value: sensors[s],
              onChanged: (val) => setState(() => sensors[s] = val ?? false),
            ),
          ),
          ElevatedButton(
            onPressed: () {
              // TODO: send selected sensors and pins to Python backend via API.
              debugPrint("Selected sensors: $sensors, pins: $pins");
            },
            child: const Text("Generate ESP Code"),
          ),
          const SizedBox(height: 20),
          const Text("Real-Time Data Visualization Placeholder"),
        ],
      ),
    );
  }
}

