import 'package:flutter/foundation.dart'; // Thêm để dùng kDebugMode
import 'package:flutter/material.dart';
import 'package:predict_ai/home_page.dart';
import 'package:predict_ai/web_socket.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    Widget home = const HomePage();

    if (kDebugMode) {
      home = Banner(
        message: 'RUN MODE', 
        location: BannerLocation.topEnd,
        color: Colors.redAccent,
        textStyle: const TextStyle(
          fontWeight: FontWeight.bold,
          fontSize: 8,
          letterSpacing: 1,
        ),
        child: home,
      );
    }

    return MaterialApp(
      debugShowCheckedModeBanner: false, // Tắt banner mặc định
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: home,
    );
  }
}
