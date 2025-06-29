import 'package:flutter/material.dart';
import 'package:predict_ai/Widget/websocketmanager.dart';
import 'package:predict_ai/constant/constant.dart';

class DrawerMenu extends StatefulWidget {
  final Function(int) onItemSelected;
  const DrawerMenu({super.key, required this.onItemSelected});

  @override
  State<DrawerMenu> createState() => _DrawerMenuState();
}

class _DrawerMenuState extends State<DrawerMenu> {
  int selectedIndex = 0;
  final WebSocketManager _wsManager = WebSocketManager();
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: Container(
            color: MyColor.appBarColor,
            child: SingleChildScrollView(
              
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Container(
                    height: 100,
                    alignment: Alignment.center,
                    width: double.infinity,
                    padding: EdgeInsets.only(top: 0),
                    child: SizedBox(
                      height: 90,
                      width: 90,
                      child: Image.asset('assets/images/LogoPREMO.png'),
                    ),
                  ),
                  SizedBox(height: 50),
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        selectedIndex = 1;
                      });
                      widget.onItemSelected(1);
                    },
                    child: Container(
                      width: double.infinity,
                      color: Colors.transparent,
                      child: Row(
                        children: [
                          Padding(
                            padding: EdgeInsetsGeometry.only(left: 20),
                            child: Icon(
                              Icons.home,
                              color:
                                  selectedIndex == 1
                                         ? Colors.white
                                      : MyColor.drawerButtonColor,
                            ),
                          ),
                          SizedBox(width: 20),
                          Container(
                            height: 40,
                            width: 3,
                            decoration: BoxDecoration(
                              color:
                                  selectedIndex == 1
                                      ? Colors.orange
                                      : Colors.transparent,
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 10),
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        selectedIndex = 2;
                      });
                      widget.onItemSelected(2);
                    },
                    child: Container(
                      width: double.infinity,
                      color: Colors.transparent,
                      child: Row(
                        children: [
                          Padding(
                            padding: EdgeInsetsGeometry.only(left: 20),
                            child: Icon(
                              Icons.settings,
                              color:
                                  selectedIndex == 2
                                            ? Colors.white
                                      : MyColor.drawerButtonColor,
                            ),
                          ),
                          SizedBox(width: 20),
                          Container(
                            height: 40,
                            width: 3,
                            decoration: BoxDecoration(
                              color:
                                  selectedIndex == 2
                                      ? Colors.orange
                                      : Colors.transparent,
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 10),
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        selectedIndex = 3;
                      });
                      widget.onItemSelected(3);
                    },
                    child: Container(
                      width: double.infinity,
                      color: Colors.transparent,
                      child: Row(
                        children: [
                          Padding(
                            padding: EdgeInsetsGeometry.only(left: 20),
                            child: Icon(
                              Icons.connecting_airports_rounded,
                              color:
                                  selectedIndex == 3
                                             ? Colors.white
                                      : MyColor.drawerButtonColor,
                            ),
                          ),
                          SizedBox(width: 20),
                          Container(
                            height: 40,
                            width: 3,
                            decoration: BoxDecoration(
                              color:
                                  selectedIndex == 3
                                      ? Colors.orange
                                      : Colors.transparent,
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 10),
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        selectedIndex = 4;
                      });
                      widget.onItemSelected(4);
                    },
                    child: Container(
                      width: double.infinity,
                      color: Colors.transparent,
                      child: Row(
                        children: [
                          Padding(
                            padding: EdgeInsetsGeometry.only(left: 20),
                            child: Icon(
                              Icons.terminal,
                              color:
                                  selectedIndex == 4
                                      ? Colors.white
                                      : MyColor.drawerButtonColor,
                            ),
                          ),
                          SizedBox(width: 20),
                          Container(
                            height: 40,
                            width: 3,
                            decoration: BoxDecoration(
                              color:
                                  selectedIndex == 4
                                      ? Colors.orange
                                      : Colors.transparent,
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
          
                  SizedBox(height: 100),
                  GestureDetector(
                    onTap: (){
                       _wsManager.send("capture");
                      
                    },
                    child: Icon(Icons.lan_rounded,color: const Color.fromARGB(255, 108, 248, 113),)),
                  SizedBox(height: 20),
                  Icon(Icons.camera_enhance,color: const Color.fromARGB(255, 108, 248, 113)),
                  SizedBox(height: 20),
                  Icon(Icons.device_hub,color: const Color.fromARGB(255, 108, 248, 113)),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
