import 'package:flutter/material.dart';

class SystemStatusBar extends StatelessWidget {
  final int activeCameras;
  final int totalCameras;
  final double cpuUsage;
  final double ramUsage;
  final double storageUsage;
  final bool systemOK;

  const SystemStatusBar({
    super.key,
    required this.activeCameras,
    required this.totalCameras,
    required this.cpuUsage,
    required this.ramUsage,
    required this.storageUsage,
    required this.systemOK,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 20,
      runSpacing: 5,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        _buildTag(
          icon: Icons.wifi,
          text: '$activeCameras/$totalCameras Online',
          color: Colors.green,
        ),
        _buildTag(
          icon: Icons.memory,
          text: 'CPU: ${cpuUsage.toStringAsFixed(0)}%',
          color: Colors.blueAccent,
        ),
        _buildTag(
          icon: Icons.sd_storage,
          text: 'Storage: ${storageUsage.toStringAsFixed(0)}%',
          color: Colors.amber.shade700,
        ),
        _buildTag(
  icon: Icons.developer_board,
  text: 'RAM: ${ramUsage.toStringAsFixed(0)}%',
  color: Colors.purpleAccent,
),
        _buildTag(
          icon: Icons.monitor_heart,
          text: systemOK ? 'System OK' : 'System Error',
          color: systemOK ? Colors.green : Colors.red,
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.circle, size: 10, color: Colors.green),
            SizedBox(width: 4),
            Text(
              'Live System',
              style: TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTag({
    required IconData icon,
    required String text,
    required Color color,
  }) {
    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.6)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(
            text,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
