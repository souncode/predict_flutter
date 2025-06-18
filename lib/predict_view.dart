import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:predict_ai/widget/camera_image.dart';
import 'package:predict_ai/constant/constant.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class PredictView extends StatefulWidget {
  final Function(int) onConnectStatus;
  const PredictView({super.key, required this.onConnectStatus});

  @override
  State<PredictView> createState() => _PredictViewState();
}

class _PredictViewState extends State<PredictView> {
  late WebSocketChannel _channel;

  Map<String, String> cameraImages = {}; // camera name -> base64 image

  @override
  void initState() {
    super.initState();
    _connectWebSocket();
  }

  void _connectWebSocket() {
    print("🔄 Connect to WebSocket...");

    _channel = WebSocketChannel.connect(
      Uri.parse('ws://172.20.10.3:8000/ws/image'),
    );

    _channel.stream.listen(
      (data) {
        final decoded = jsonDecode(data);
        final String cameraName = decoded['camera'];
        final String image = decoded['image'];

        setState(() {
          cameraImages[cameraName] = image;
        });
      },
      onError: (error) {
        print("⚠️ WebSocket Error: $error");
        _reconnectWebSocket();
      },
      onDone: () {
        print("❌ WebSocket closed.");
        _reconnectWebSocket();
      },
      cancelOnError: true,
    );
  }

  void _reconnectWebSocket() async {
    await Future.delayed(const Duration(seconds: 2));
    _connectWebSocket();
  }

  @override
  void dispose() {
    _channel.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cameraNames = cameraImages.keys.toList();

    return Scaffold(
      backgroundColor: MyColor.backgroundColor,
      body: SafeArea(
        child: Row(
          children: [
            Expanded(
              flex: 8,
              child: GridView.count(
                crossAxisCount: 3,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
                padding: const EdgeInsets.all(12),
                children:
                    cameraNames.map((cameraName) {
                      return CameraImageWidget(
                        cameraId: cameraName,
                        base64Image: cameraImages[cameraName],
                      );
                    }).toList(),
              ),
            ),
            const Expanded(flex: 1, child: SizedBox()),
            ElevatedButton(
              onPressed: () {
                _channel.sink.add("capture");
                print("📤 Sent command capture");
              },
              child: const Text("Shot"),
            ),
          ],
        ),
      ),
    );
  }
}
