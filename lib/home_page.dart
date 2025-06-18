import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:predict_ai/about_page.dart';
import 'package:predict_ai/config_page.dart';
import 'package:predict_ai/connection_page.dart';
import 'package:predict_ai/predict_view.dart';
import 'package:predict_ai/widget/camera_image.dart';
import 'package:predict_ai/widget/drawer_menu.dart';
import 'package:predict_ai/constant/constant.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:math';
import 'package:google_fonts/google_fonts.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late WebSocketChannel _channel;
  int _currentPage = 1;
  int _wsStatus =0;
  Map<String, String> cameraImages = {}; // camera name -> base64 image

  @override
  void initState() {
    super.initState();
    _channel = WebSocketChannel.connect(
      Uri.parse('ws://172.20.10.3:8000/ws/image'),
    );

    _channel.stream.listen(
      (data) {
        print("Receive");
        final decoded = jsonDecode(data);
        final String cameraName = decoded['camera'];
        final String image = decoded['image'];
        setState(() {
          cameraImages[cameraName] = image;
        });
      },
      onError: (error) {
        print("❌ [Flutter] Lỗi WebSocket: $error");
      },
      onDone: () {
        print("❌ [Flutter] WebSocket đã đóng");
      },
    );
  }

  @override
  void dispose() {
    _channel.sink.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cameraNames = cameraImages.keys.toList();

    return Scaffold(
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
                color: MyColor.iconGrayColor,
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
            const Expanded(flex: 1, child: SizedBox()),
          ],
        ),
      ),
    );
  }
}
