import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
class WebSocketManager {
  static final WebSocketManager _instance = WebSocketManager._internal();
  factory WebSocketManager() => _instance;

  late WebSocketChannel _channel;
  bool _isConnected = false;

  final ValueNotifier<Map<String, String>> cameraImages = ValueNotifier({});

  WebSocketManager._internal() {
    _connect();
  }

  void _connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://192.168.1.11:8000/ws/image'),
    );

    _channel.stream.listen(
      (data) {
        final decoded = jsonDecode(data);
        final String camera = decoded['camera'];
        final String image = decoded['image'];

        final current = Map<String, String>.from(cameraImages.value);
        current[camera] = image;
        cameraImages.value = current; // 👈 Trigger update
        print("📥 Updated image from $camera");
      },
      onError: (error) {
        print("⚠️ WebSocket error: $error");
        _reconnect();
      },
      onDone: () {
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
  }
}
