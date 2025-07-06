import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:predict_ai/Widget/system_status.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketManager {
  static final WebSocketManager _instance = WebSocketManager._internal();
  factory WebSocketManager() => _instance;

  late WebSocketChannel _channel;
  bool _isConnected = false;
  final ValueNotifier<Map<String, String>> cameraImages = ValueNotifier({});
  final ValueNotifier<double> avgProcessing = ValueNotifier(0);
  final ValueNotifier<double> totalProcessing = ValueNotifier(0);
  final ValueNotifier<int> totalDetections = ValueNotifier(0);
  final ValueNotifier<int> activeCameras = ValueNotifier(0);
  final ValueNotifier<int> cameraOnline = ValueNotifier(0);
  final ValueNotifier<double> cpuUsage = ValueNotifier(0);
  final ValueNotifier<double> storageUsage = ValueNotifier(0);
  final ValueNotifier<bool> systemOk = ValueNotifier(true);
  final ValueNotifier<bool> isConnectedNotifier = ValueNotifier(false);
  List<dynamic> cameraConfigs = [];

  void loadCameraConfig() async {
    final configJson = await rootBundle.loadString(
      'GrabImage/CameraConfig.json',
    );
    final config = jsonDecode(configJson);
    cameraConfigs = config['cameras'];
  }

  WebSocketManager._internal() {
    _connect();
  }

  void _connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://192.168.1.11:8000/ws/image'),
    );

    _channel.stream.listen(
      (data) {
        isConnectedNotifier.value = true;
        try {
          final decoded = jsonDecode(data);

          if (decoded['type'] == 'processing_summary' &&
              decoded.containsKey('total_processing')) {
            totalProcessing.value = decoded['total_processing'].toDouble();
            print("📊 Updated total processing: ${totalProcessing.value} ms");
          }

          // 🖼️ Cập nhật ảnh nếu có
          if (decoded.containsKey('camera') && decoded.containsKey('image')) {
            final String camera = decoded['camera'];
            final String image = decoded['image'];

            final current = Map<String, String>.from(cameraImages.value);
            current[camera] = image;
            cameraImages.value = current;
            print("📥 Updated image from $camera");
          }

          if (decoded['type'] == 'processing_summary') {
            totalDetections.value++;
            print(
              "🔁 +1 lần xử lý → Total Detections: ${totalDetections.value}",
            );
            totalProcessing.value =
                decoded['total_processing']?.toDouble() ?? 0;
            if (decoded.containsKey('total_cameras')) {
              activeCameras.value = decoded['total_cameras'];
              print("📸 Số camera hoạt động: ${activeCameras.value}");
            }
          }
          if (decoded['type'] == 'system_status') {
            systemMetricsNotifier.value = SystemMetrics(
              activeCameras: decoded['active'] ?? 0,
              totalCameras: decoded['total'] ?? 0,
              cpuUsage: (decoded['cpu'] ?? 0).toDouble(),
              ramUsage: (decoded['ram'] ?? 0).toDouble(),
              storageUsage: (decoded['storage'] ?? 0).toDouble(),
              systemOK: decoded['system_ok'] ?? true,
            );
          }
        } catch (e) {
          print("❌ Error decoding WebSocket message: $e");
        }
      },
      onError: (error) {
        isConnectedNotifier.value = false;
        print("⚠️ WebSocket error: $error");
        _reconnect();
      },
      onDone: () {
        isConnectedNotifier.value = false;
        print("❌ WebSocket closed.");
        _reconnect();
      },
      cancelOnError: true,
    );

    _isConnected = true;
  }

  void _reconnect() async {
    _isConnected = false;
    await Future.delayed(const Duration(seconds: 2));
    _connect();
  }

  void send(String message) {
    if (_isConnected) {
      _channel.sink.add(message);
      print("📤 Sent message: $message");
    } else {
      print("🚫 WebSocket not connected.");
    }
  }

  void dispose() {
    _channel.sink.close();
    cameraImages.dispose();
    avgProcessing.dispose();
  }
}
