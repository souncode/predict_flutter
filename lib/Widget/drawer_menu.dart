import 'package:flutter/material.dart';
import 'package:predict_ai/constant/constant.dart';

class DrawerMenu extends StatefulWidget {
  const DrawerMenu({super.key});

  @override
  State<DrawerMenu> createState() => _DrawerMenuState();
}

class _DrawerMenuState extends State<DrawerMenu> {
  int selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          height: MediaQuery.of(context).size.height,
          color: MyColor.secondaryBgColor,
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
                                    ? Colors.black
                                    : MyColor.iconGrayColor,
                          ),
                        ),
                        SizedBox(width: 20),
                        Container(
                          height: 40,
                          width: 3,
                          decoration: BoxDecoration(
                            color:
                                selectedIndex == 1
                                    ? Colors.black
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
                                    ? Colors.black
                                    : MyColor.iconGrayColor,
                          ),
                        ),
                        SizedBox(width: 20),
                        Container(
                          height: 40,
                          width: 3,
                          decoration: BoxDecoration(
                            color:
                                selectedIndex == 2
                                    ? Colors.black
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
                                    ? Colors.black
                                    : MyColor.iconGrayColor,
                          ),
                        ),
                        SizedBox(width: 20),
                        Container(
                          height: 40,
                          width: 3,
                          decoration: BoxDecoration(
                            color:
                                selectedIndex == 3
                                    ? Colors.black
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
                  },
                  child: Container(
                    width: double.infinity,
                    color: Colors.transparent,
                    child: Row(
                      children: [
                        Padding(
                          padding: EdgeInsetsGeometry.only(left: 20),
                          child: Icon(
                            Icons.person,
                            color:
                                selectedIndex == 4
                                    ? Colors.black
                                    : MyColor.iconGrayColor,
                          ),
                        ),
                        SizedBox(width: 20),
                        Container(
                          height: 40,
                          width: 3,
                          decoration: BoxDecoration(
                            color:
                                selectedIndex == 4
                                    ? Colors.black
                                    : Colors.transparent,
                            borderRadius: BorderRadius.circular(5),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 10),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
