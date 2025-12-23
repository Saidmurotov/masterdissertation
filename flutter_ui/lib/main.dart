import 'dart:convert';
import 'dart:math';

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  ThemeMode mode = ThemeMode.dark;

  void _toggleTheme() {
    setState(() {
      mode = mode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DAQ Sensor Dashboard',
      themeMode: mode,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueGrey,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: SensorSelectionPage(onToggleTheme: _toggleTheme, mode: mode),
    );
  }
}

class SensorSelectionPage extends StatefulWidget {
  const SensorSelectionPage({super.key, required this.onToggleTheme, required this.mode});

  final VoidCallback onToggleTheme;
  final ThemeMode mode;

  @override
  State<SensorSelectionPage> createState() => _SensorSelectionPageState();
}

class _SensorSelectionPageState extends State<SensorSelectionPage> {
  List<Map<String, dynamic>> availableSensors = [];
  final Map<String, bool> selected = {};
  final Map<String, TextEditingController> pinControllers = {};
  final List<String> boards = const ["ESP32", "ESP8266", "Arduino Uno"];
  String selectedBoard = "ESP32";
  bool isLoading = false;
  bool sensorsLoading = true;
  String? generatedCode;
  List<String> semanticErrors = [];
  WebSocketChannel? channel;

  // Live data buffers
  final List<FlSpot> tempSeries = [];
  final List<FlSpot> humSeries = [];
  final List<FlSpot> pressureSeries = [];
  final List<FlSpot> gasSeries = [];
  final List<FlSpot> lightSeries = [];
  double tick = 0;
  static const int maxPoints = 50;

  @override
  void initState() {
    super.initState();
    _loadSensors();
    _connectStream();
  }

  @override
  void dispose() {
    for (final c in pinControllers.values) {
      c.dispose();
    }
    channel?.sink.close();
    super.dispose();
  }

  void _connectStream() {
    channel = WebSocketChannel.connect(Uri.parse("ws://127.0.0.1:8000/ws/data"));
    channel!.stream.listen((event) {
      try {
        final data = jsonDecode(event);
        _ingestData(data);
      } catch (_) {
        // ignore parse errors
      }
    }, onError: (e) {
      _showSnack("Stream error: $e");
    });
  }

  void _ingestData(Map<String, dynamic> data) {
    setState(() {
      tick += 1;
      void addPoint(List<FlSpot> series, num? v) {
        if (v == null) return;
        series.add(FlSpot(tick, v.toDouble()));
        if (series.length > maxPoints) {
          series.removeAt(0);
        }
      }

      addPoint(tempSeries, data["temperature"]);
      addPoint(humSeries, data["humidity"]);
      addPoint(pressureSeries, data["pressure"]);
      addPoint(gasSeries, data["gas"]);
      addPoint(lightSeries, data["light"]);
    });
  }

  Future<void> _loadSensors() async {
    setState(() => sensorsLoading = true);
    try {
      final resp = await http.get(Uri.parse("http://127.0.0.1:8000/sensors"));
      if (resp.statusCode == 200) {
        final List<dynamic> data = jsonDecode(resp.body);
        availableSensors = data.cast<Map<String, dynamic>>();
        for (final s in availableSensors) {
          final type = s["type"] as String;
          selected[type] = false;
          if (s["requires_pin"] == true) {
            final defPin = s["default_pin"];
            pinControllers[type] =
                TextEditingController(text: defPin != null ? "$defPin" : "");
          }
        }
      } else {
        _showSnack("Failed to load sensors: ${resp.statusCode}");
      }
    } catch (e) {
      _showSnack("Failed to load sensors: $e");
    } finally {
      setState(() => sensorsLoading = false);
    }
  }

  Future<void> _generateCode() async {
    final selectedTypes =
        selected.entries.where((e) => e.value).map((e) => e.key).toList();
    if (selectedTypes.isEmpty) {
      _showSnack("Please select at least one sensor.");
      return;
    }

    final sensorPayload = selectedTypes.map((sType) {
      final meta = availableSensors.firstWhere((m) => m["type"] == sType);
      final payload = {"type": sType};
      if (meta["requires_pin"] == true) {
        final txt = pinControllers[sType]?.text ?? "";
        final pin = int.tryParse(txt);
        if (pin != null) {
          payload["pin"] = pin;
        }
      }
      return payload;
    }).toList();

    setState(() => isLoading = true);
    try {
      final uri = Uri.parse("http://127.0.0.1:8000/generate-code");
      final resp = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "mcu": selectedBoard,
          "board": selectedBoard,
          "sensors": sensorPayload,
          // placeholders for logic checks; wire real values when available
          "mqtt_enabled": true,
          "wifi_ssid": "demo-ssid",
          "wifi_password": "demo-pass",
          "mqtt_broker": "mqtt.local",
        }),
      );

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        setState(() {
          generatedCode = data["code"] as String?;
          semanticErrors = [];
        });
        if (generatedCode != null) {
          _showCodeDialog(generatedCode!);
        }
      } else {
        _handleError(resp);
      }
    } catch (e) {
      _showSnack("Request failed: $e");
    } finally {
      setState(() => isLoading = false);
    }
  }

  void _handleError(http.Response resp) {
    try {
      final data = jsonDecode(resp.body);
      final errors = data is Map && data["detail"] is Map
          ? (data["detail"]["semantic_errors"] as List?)?.cast<String>()
          : null;
      if (errors != null && errors.isNotEmpty) {
        setState(() => semanticErrors = errors);
        _showSemanticDialog(errors);
        return;
      }
    } catch (_) {
      // ignore and fallthrough
    }
    _showSnack("Backend error: ${resp.statusCode} ${resp.body}");
  }

  void _showSemanticDialog(List<String> errors) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Semantic Validation Errors"),
          content: SizedBox(
            width: double.maxFinite,
            child: ListView(
              shrinkWrap: true,
              children: errors.map((e) => Text("- $e")).toList(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text("Close"),
            ),
          ],
        );
      },
    );
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  void _showCodeDialog(String code) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text("Generated ESP Code"),
          content: SizedBox(
            width: double.maxFinite,
            child: SingleChildScrollView(
              child: SelectableText(code),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text("Close"),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Sensor Selection")),
      body: sensorsLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        "DAQ Control & Monitoring",
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      IconButton(
                        tooltip: "Toggle theme",
                        onPressed: widget.onToggleTheme,
                        icon: Icon(widget.mode == ThemeMode.dark
                            ? Icons.light_mode
                            : Icons.dark_mode),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Card(
                    elevation: 2,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "Select Sensors",
                            style:
                                TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          DropdownButtonFormField<String>(
                            value: selectedBoard,
                            decoration: const InputDecoration(labelText: "Board"),
                            items: boards
                                .map((b) =>
                                    DropdownMenuItem(value: b, child: Text(b)))
                                .toList(),
                            onChanged: (val) {
                              if (val != null) {
                                setState(() => selectedBoard = val);
                              }
                            },
                          ),
                          const SizedBox(height: 12),
                          ...availableSensors.map((s) {
                            final type = s["type"] as String;
                            final requiresPin = s["requires_pin"] == true;
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                CheckboxListTile(
                                  title: Text(type),
                                  value: selected[type] ?? false,
                                  onChanged: (val) =>
                                      setState(() => selected[type] = val ?? false),
                                ),
                                if (requiresPin)
                                  Padding(
                                    padding: const EdgeInsets.only(left: 16, right: 16),
                                    child: TextField(
                                      controller: pinControllers[type],
                                      keyboardType: TextInputType.number,
                                      decoration: const InputDecoration(
                                        labelText: "Pin",
                                        hintText: "e.g., 4",
                                      ),
                                    ),
                                  ),
                                const Divider(),
                              ],
                            );
                          }),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Card(
                    elevation: 2,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "Actions",
                            style:
                                TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          ElevatedButton(
                            onPressed: isLoading ? null : _generateCode,
                            style: ElevatedButton.styleFrom(
                              minimumSize: const Size.fromHeight(48),
                            ),
                            child: isLoading
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : const Text("Generate ESP Code"),
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (semanticErrors.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Card(
                      color: Colors.amber.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "Semantic Warnings",
                              style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.amber.shade900),
                            ),
                            const SizedBox(height: 8),
                            ...semanticErrors.map((e) => Text("• $e")),
                          ],
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                  _chartsSection(context),
                ],
              ),
            ),
    );
  }

  Widget _chartsSection(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "Live Telemetry",
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _chartCard(
              title: "Temperature / Humidity",
              series: [
                _Series(name: "Temp", data: tempSeries, color: Colors.orange),
                _Series(name: "Humidity", data: humSeries, color: Colors.blue),
              ],
            ),
            _chartCard(
              title: "Pressure",
              series: [
                _Series(name: "Pressure", data: pressureSeries, color: Colors.cyan),
              ],
            ),
            _chartCard(
              title: "Air Quality / Light",
              series: [
                _Series(name: "Gas", data: gasSeries, color: Colors.green),
                _Series(name: "Light", data: lightSeries, color: Colors.yellow),
              ],
            ),
          ],
        ),
      ],
    );
  }

  Widget _chartCard({required String title, required List<_Series> series}) {
    return SizedBox(
      width: 380,
      height: 260,
      child: Card(
        elevation: 2,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Expanded(
                child: LineChart(
                  LineChartData(
                    backgroundColor: Colors.transparent,
                    gridData: const FlGridData(show: true),
                    titlesData: const FlTitlesData(
                      bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 38)),
                      rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    ),
                    lineBarsData: series
                        .map(
                          (s) => LineChartBarData(
                            spots: s.data,
                            isCurved: true,
                            color: s.color,
                            barWidth: 2,
                            dotData: const FlDotData(show: false),
                          ),
                        )
                        .toList(),
                    borderData: FlBorderData(
                      show: true,
                      border: Border.all(color: Colors.grey.withOpacity(0.3)),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Series {
  _Series({required this.name, required this.data, required this.color});
  final String name;
  final List<FlSpot> data;
  final Color color;
}

