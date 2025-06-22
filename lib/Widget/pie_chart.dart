import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class PieChartRate extends StatelessWidget {
  final int okCount;
  final int ngCount;

  const PieChartRate({super.key, required this.okCount, required this.ngCount});

  @override
  Widget build(BuildContext context) {
    final total = okCount + ngCount;
    return PieChart(
      PieChartData(
        sections: [
          PieChartSectionData(
            value: okCount.toDouble(),
            title: 'OK\n${((okCount / total) * 100).toStringAsFixed(1)}%',
            color: Colors.green,
            radius: 60,
            titleStyle: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          PieChartSectionData(
            value: ngCount.toDouble(),
            title: 'NG\n${((ngCount / total) * 100).toStringAsFixed(1)}%',
            color: Colors.red,
            radius: 60,
            titleStyle: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
        sectionsSpace: 4,
        centerSpaceRadius: 40,
      ),
    );
  }
}
