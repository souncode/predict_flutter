import 'package:flutter/material.dart';

class DashboardStats extends StatelessWidget {
  const DashboardStats({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildStatCard(
          icon: Icons.visibility,
          title: 'Total Detections',
          value: '1.273',
          iconColor: Colors.blueAccent,
        ),
        _buildStatCard(
          icon: Icons.check_circle,
          title: 'Pass Rate',
          value: '94.2%',
          valueColor: Colors.greenAccent,
          showProgressBar: true,
          progress: 0.942,
        ),
        _buildStatCard(
          icon: Icons.videocam,
          title: 'Active Cameras',
          value: '6/6',
          iconColor: Colors.greenAccent,
          dots: 6,
        ),
        _buildStatCard(
          icon: Icons.timer,
          title: 'Avg Processing',
          value: '156ms',
          valueColor: Colors.amber,
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
                  child: Icon(Icons.fiber_manual_record,
                      size: 10, color: Colors.greenAccent),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
