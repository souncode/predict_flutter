import 'package:flutter/material.dart';
import 'package:predict_ai/widget/drawer_menu.dart';
import 'package:predict_ai/constant/constant.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MyColor.backgroundColor,
      body: SafeArea(
        child: Row(
          children: [
            SizedBox(width: 70, child: DrawerMenu()),
            Expanded(flex: 0, child: SizedBox()),
            Expanded(flex: 4, child: SizedBox()),
          ],
        ),
      ),
    );
  }
}
