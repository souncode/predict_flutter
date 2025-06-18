import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/material.dart';

class CameraImageWidget extends StatelessWidget {
  final String cameraId;        // 👈 đổi từ int -> String
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
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(6),
            child: Text(
              cameraId, // 👈 hiển thị tên camera luôn
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: bytes != null
                ? Image.memory(bytes, fit: BoxFit.cover)
                : const Center(child: Text("No image")),
          ),
        ],
      ),
    );
  }
}
