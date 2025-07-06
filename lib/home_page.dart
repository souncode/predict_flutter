import 'package:flutter/material.dart';
import 'package:predict_ai/Widget/dashboardstats.dart';
import 'package:predict_ai/Widget/system_status.dart';
import 'package:predict_ai/Widget/systemstatusbar.dart';
import 'package:predict_ai/about_page.dart';
import 'package:predict_ai/config_page.dart';
import 'package:predict_ai/connection_page.dart';
import 'package:predict_ai/predict_view.dart';
import 'package:predict_ai/widget/drawer_menu.dart';
import 'package:predict_ai/constant/constant.dart';
import 'package:google_fonts/google_fonts.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _currentPage = 1;
  Map<String, String> cameraImages = {}; // camera name -> base64 image

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Column(
              children: [
                Text(
                  "Premo Industrial Vision Dashboard",
                  style: GoogleFonts.lilitaOne(color: Color(0xFF60A5FA)),
                ),
                Text(
                  "AI-Powered 6-Camera Inspection System",
                  style: TextStyle(
                    fontSize: 10,
                    color: Color.fromARGB(255, 137, 148, 161),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            Spacer(),
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: ValueListenableBuilder<SystemMetrics>(
                valueListenable: systemMetricsNotifier,
                builder: (context, metrics, _) {
                  return SystemStatusBar(
                    cpuUsage: metrics.cpuUsage,
                    ramUsage: metrics.ramUsage,
                    storageUsage: metrics.storageUsage,
                    systemOK: metrics.systemOK,
                  );
                },
              ),
            ),
          ],
        ),
        backgroundColor: MyColor.appBarColor,
      ),
      backgroundColor: MyColor.backgroundColor,
      body: SafeArea(
        child: Row(
          children: [
            SizedBox(
              width: 70,
              child: DrawerMenu(
                onItemSelected: (int index) {
                  setState(() {
                    _currentPage = index;
                  });
                },
              ),
            ),
            SizedBox(
              width: 50,
              height: double.infinity,
              child: Container(
                color: const Color.fromARGB(255, 40, 53, 73),
                child: Center(
                  // Thêm Center để căn giữa
                  child: RotatedBox(
                    quarterTurns: -1, // hoặc 3
                    child: Text(
                      _currentPage == 1
                          ? "Home Page"
                          : _currentPage == 2
                          ? "Setting"
                          : _currentPage == 3
                          ? "Connection"
                          : "Log",
                      style: GoogleFonts.alfaSlabOne(
                        color: Colors.white,
                        fontSize: 20,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            Expanded(
              flex: 8,
              child:
                  _currentPage == 1
                      ? PredictView(
                        onConnectStatus: (int index) {
                          setState(() {
                            _currentPage = index;
                          });
                        },
                      )
                      : _currentPage == 2
                      ? ConfigPage()
                      : _currentPage == 3
                      ? ConnectionPage()
                      : LogPage(),
            ),
            Expanded(
              flex: 2,
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(4.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [DashboardStats(), Text("Real-time Analytics")],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
