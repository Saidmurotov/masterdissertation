import 'package:flutter/material.dart';
import '../services/backend_manager.dart';
import '../utils/branding.dart';
import '../main.dart'; // Import to navigate to SensorSelectionPage

class SplashScreen extends StatefulWidget {
  final VoidCallback onReady;
  const SplashScreen({super.key, required this.onReady});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  String status = "Initializing Semantic Engine...";
  double progress = 0.0;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    // 1. Start Backend
    setState(() {
      status = "Starting DAQ Background Service...";
      progress = 0.2;
    });
    await BackendManager.start();

    // 2. Wait for Backend
    setState(() {
      status = "Connecting to Local Intelligence Node...";
      progress = 0.4;
    });
    int retries = 0;
    while (retries < 20) {
      // Wait up to ~10-20 seconds
      if (await BackendManager.isReady()) {
        break;
      }
      await Future.delayed(const Duration(milliseconds: 500));
      retries++;
      if (retries % 4 == 0) {
        setState(() {
          progress += 0.1;
        });
      }
    }

    // 3. Complete
    setState(() {
      status = "Ready";
      progress = 1.0;
    });
    await Future.delayed(const Duration(milliseconds: 500));

    widget.onReady();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.blueGrey.shade900,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.settings_input_component,
                size: 80, color: Colors.cyanAccent),
            const SizedBox(height: 24),
            const Text(
              Branding.appTitle,
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              Branding.appSubtitle,
              style: TextStyle(color: Colors.white70, fontSize: 16),
            ),
            const SizedBox(height: 48),
            SizedBox(
              width: 250,
              child: LinearProgressIndicator(
                value: progress,
                backgroundColor: Colors.white24,
                valueColor:
                    const AlwaysStoppedAnimation<Color>(Colors.cyanAccent),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              status,
              style: const TextStyle(color: Colors.white54, fontSize: 14),
            ),
            const SizedBox(height: 60),
            const Text(
              Branding.developerCredit,
              style: TextStyle(color: Colors.white30, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
