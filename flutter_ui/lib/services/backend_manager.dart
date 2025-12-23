import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;

class BackendManager {
  static Process? _process;
  static const String _host = "127.0.0.1";
  static const int _port = 8000;

  /// Start the backend_server.exe sidecar process
  static Future<void> start() async {
    if (_process != null) return;

    // In a packaged app, the exe should be in the same directory.
    // In debug mode, we might just assume it's running or try to run python.
    // For this context, we'll try to spawn the exe or python script.

    // We strive to find the executable relative to the running one.
    final exePath =
        p.join(p.dirname(Platform.resolvedExecutable), 'backend_server.exe');

    print("Attempting to start backend from: $exePath");
    if (await File(exePath).exists()) {
      _process = await Process.start(exePath, [], runInShell: false);
    } else {
      // Fallback for development (assuming running from root of project via IDE or terminal)
      // This path is tricky in dev, often better to just run python manually,
      // but we can try to find the project root if we are in flutter_ui.
      print(
          "backend_server.exe not found. Assuming development mode (manual start expected or skipped).");
    }
  }

  /// Stop the backend process
  static void stop() {
    print("Stopping backend...");
    _process?.kill();
    // Force kill to be safe on Windows
    Process.run('taskkill', ['/F', '/IM', 'backend_server.exe']);
  }

  /// Ping the backend to see if it's ready
  static Future<bool> isReady() async {
    try {
      final resp = await http.get(Uri.parse("http://$_host:$_port/docs"));
      return resp.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
