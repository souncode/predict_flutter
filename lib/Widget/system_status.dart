import 'package:flutter/foundation.dart';

class SystemMetrics {
  final double cpuUsage;
  final double storageUsage;
  final double ramUsage;
  final bool systemOK;

  SystemMetrics({
    required this.cpuUsage,
    required this.storageUsage,
    required this.ramUsage,
    required this.systemOK,
  });
}

final ValueNotifier<SystemMetrics> systemMetricsNotifier = ValueNotifier(
  SystemMetrics(
    cpuUsage: 0.0,
    ramUsage: 0.0,
    storageUsage: 0.0,
    systemOK: true,
  ),
);
