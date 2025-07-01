import 'package:flutter/material.dart';
import 'package:predict_ai/Widget/websocketmanager.dart';

import 'package:predict_ai/widget/camera_image.dart';
import 'package:predict_ai/constant/constant.dart';

class PredictView extends StatefulWidget {
  final Function(int) onConnectStatus;
  const PredictView({super.key, required this.onConnectStatus});

  @override
  State<PredictView> createState() => _PredictViewState();
}

class _PredictViewState extends State<PredictView> {
  final WebSocketManager _ws = WebSocketManager();

  @override
  void initState() {
    super.initState();
    print("✅ PredictView initialized");
  }

  void _sendCaptureCommand() {
    _ws.send("capture");
    print("📤 Sent command: capture");
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MyColor.backgroundColor,
      body: SafeArea(
        child: Row(
          children: [
            Expanded(
              flex: 8,
              child: ValueListenableBuilder<Map<String, String>>(
                valueListenable: _ws.cameraImages,
                builder: (context, cameraImages, _) {
                  final cameraNames = cameraImages.keys.toList();

                  return GridView.count(
                    crossAxisCount: 3,
                    crossAxisSpacing: 8,
                    mainAxisSpacing: 8,
                    padding: const EdgeInsets.all(12),
                    children: cameraNames.map((cameraName) {
                      return CameraImageWidget(
                        cameraId: cameraName,
                        base64Image: cameraImages[cameraName],
                      );
                    }).toList(),
                  );
                },
              ),
            ),

            
           
          ],
        ),
      ),
    );
  }
}
