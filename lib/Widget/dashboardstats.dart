import 'package:flutter/material.dart';
import 'package:predict_ai/Widget/pie_chart.dart';
import 'package:predict_ai/Widget/system_status.dart';
import 'package:predict_ai/services/websocketmanager.dart'; // ✅ Import đúng

class DashboardStats extends StatefulWidget {
  const DashboardStats({super.key});

  @override
  State<DashboardStats> createState() => _DashboardStatsState();
}

class _DashboardStatsState extends State<DashboardStats> {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ValueListenableBuilder<int>(
          valueListenable: WebSocketManager().totalDetections,
          builder: (context, count, _) {
            return _buildStatCard(
              icon: Icons.visibility,
              title: 'Total Detections',
              value: '$count',
              iconColor: Colors.blueAccent,
            );
          },
        ),
        _buildStatCard(
          icon: Icons.check_circle,
          title: 'Pass Rate',
          value: '94.2%',
          valueColor: Colors.greenAccent,
          iconColor: Colors.lightGreen,
          showProgressBar: true,
          progress: 0.942,
        ),
        ValueListenableBuilder<SystemMetrics>(
          valueListenable: systemMetricsNotifier,
          builder: (context, metrics, _) {
            return _buildStatCard(
              icon: Icons.videocam,
              title: 'Active Cameras',
              value: '${metrics.activeCameras}/${metrics.totalCameras}',
              iconColor:
                  metrics.activeCameras == metrics.totalCameras
                      ? Colors.greenAccent
                      : Colors.grey,
              dots: metrics.activeCameras,
            );
          },
        ),

        // ✅ Widget realtime với WebSocketManager
        ValueListenableBuilder<double>(
          valueListenable: WebSocketManager().totalProcessing,
          builder: (context, value, _) {
            return _buildStatCard(
              iconColor: Colors.redAccent,
              icon: Icons.timer,
              title: 'Total Processing',
              value: '${value.toStringAsFixed(0)} ms',
              valueColor: Colors.amber,
            );
          },
        ),

        Container(
          margin: const EdgeInsets.symmetric(vertical: 3),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF1B2330),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Text(
                "Chart",
                style: const TextStyle(color: Colors.white70, fontSize: 14),
              ),
              SizedBox(
                height: 300,
                child: PieChartRate(okCount: 23, ngCount: 10),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String title,
    required String value,
    Color? iconColor,
    Color? valueColor,
    bool showProgressBar = false,
    double progress = 0,
    int dots = 0,
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 3),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1B2330),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: iconColor ?? Colors.white),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(color: Colors.white70, fontSize: 14),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              color: valueColor ?? Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (showProgressBar) ...[
            const SizedBox(height: 6),
            LinearProgressIndicator(
              value: progress,
              backgroundColor: Colors.white12,
              color: Colors.greenAccent,
              minHeight: 6,
              borderRadius: BorderRadius.circular(4),
            ),
          ],
          if (dots > 0)
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: List.generate(
                dots,
                (_) => Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2),
                  child: Icon(
                    Icons.fiber_manual_record,
                    size: 10,
                    color: Colors.greenAccent,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
