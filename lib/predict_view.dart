import 'package:flutter/material.dart';
import 'package:predict_ai/services/websocketmanager.dart';
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
                  if (cameraImages.isEmpty) {
                    return const Center(
                      child: CircularProgressIndicator(
                        color: Colors.blueAccent,
                      ),
                    );
                  }

                  final cameraNames = cameraImages.keys.toList();

                  return LayoutBuilder(
                    builder: (context, constraints) {
                      int cameraCount = cameraNames.length;
                      int crossAxisCount;

                      if (cameraCount == 1) {
                        crossAxisCount = 1;
                      } else if (cameraCount == 2) {
                        crossAxisCount = 2;
                      } else {
                        crossAxisCount = 3;
                      }

                      return GridView.count(
                        crossAxisCount: crossAxisCount,
                        crossAxisSpacing: 8,
                        mainAxisSpacing: 8,
                        padding: const EdgeInsets.all(12),
                        children:
                            cameraNames.map((cameraName) {
                              return AspectRatio(
                                aspectRatio: 4 / 3, 
                                child: CameraImageWidget(
                                  cameraId: cameraName,
                                  base64Image: cameraImages[cameraName],
                                ),
                              );
                            }).toList(),
                      );
                    },
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
