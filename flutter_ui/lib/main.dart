import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

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
  List<Map<String, dynamic>> availableSensors = [];
  final Map<String, bool> selected = {};
  final Map<String, TextEditingController> pinControllers = {};
  bool isLoading = false;
  bool sensorsLoading = true;
  String? generatedCode;
  List<String> semanticErrors = [];

  @override
  void initState() {
    super.initState();
    _loadSensors();
  }

  @override
  void dispose() {
    for (final c in pinControllers.values) {
      c.dispose();
    }
    super.dispose();
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
          "mcu": "ESP32",
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
                  const Text(
                    "Real-Time Data Visualization Placeholder",
                    style: TextStyle(fontSize: 16),
                  ),
                ],
              ),
            ),
    );
  }
}

