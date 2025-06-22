import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:predict_ai/constant/constant.dart';

class CameraImageWidget extends StatelessWidget {
  final String cameraId;
  final String? base64Image;

  const CameraImageWidget({
    required this.cameraId,
    this.base64Image,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    Uint8List? bytes;
    if (base64Image != null) {
      try {
        bytes = base64Decode(base64Image!);
      } catch (_) {}
    }

    return Card(
      color: MyColor.appBarColor,
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(6),
            child: Row(
              children: [
                Expanded(flex: 5, child: Icon(Icons.camera_enhance)),
                Expanded(
                  flex: 5,
                  child: Text(
                    cameraId, // 👈 hiển thị tên camera luôn
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Icon(Icons.online_prediction),
                SizedBox(width: 20),
                Container(
                  child: Padding(
                    padding: const EdgeInsets.all(3.0),
                    child: Text(" Connected "),
                  ),
                  decoration: BoxDecoration(
                    color: Colors.greenAccent,
                    borderRadius: BorderRadius.circular(15),
                  ),
                ),
                SizedBox(width: 30),
              ],
            ),
          ),
          Expanded(
            child:
                bytes != null
                    ? Image.memory(bytes, fit: BoxFit.cover)
                    : const Center(child: Text("No image")),
          ),
          Padding(
            padding: const EdgeInsets.all(6),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        "Detection",
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        "Pass",
                        style: TextStyle(fontSize: 10, color: Colors.white),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        "Confidence",
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        "99.5",
                        style: TextStyle(fontSize: 10, color: Colors.white),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        "Count",
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        "10",
                        style: TextStyle(fontSize: 10, color: Colors.white),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
