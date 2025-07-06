import 'package:flutter/foundation.dart';

class SystemMetrics {
  final int activeCameras;
  final int totalCameras;
  final double cpuUsage;
  final double storageUsage;
  final double ramUsage;
  final bool systemOK;

  SystemMetrics({
    required this.activeCameras,
    required this.totalCameras,
    required this.cpuUsage,
    required this.storageUsage,
    required this.ramUsage,
    required this.systemOK,
  });
}

final ValueNotifier<SystemMetrics> systemMetricsNotifier = ValueNotifier(
  SystemMetrics(
    activeCameras: 0,
    totalCameras: 6,
    cpuUsage: 0.0,
    ramUsage: 0.0,
    storageUsage: 0.0,
    systemOK: true,
  ),
);
