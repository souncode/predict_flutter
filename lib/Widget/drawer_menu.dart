import 'package:flutter/material.dart';
import 'package:predict_ai/constant/constant.dart';

class DrawerMenu extends StatefulWidget {
  const DrawerMenu({super.key});

  @override
  State<DrawerMenu> createState() => _DrawerMenuState();
}

class _DrawerMenuState extends State<DrawerMenu> {
  int selectedIndex=0;

  @override
  Widget build(BuildContext context) {
    return Drawer(
      elevation: 0,
      child: Container(
        height: double.infinity,
        width: double.infinity,
        color: MyColor.secondaryBgColor,
        child:  SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                height: 100,
                alignment: Alignment.center,
                width: double.infinity,
                padding: EdgeInsets.only(top:20),
                child: SizedBox(height: 40,width: 25,child: Icon(Icons.heart_broken),),
              ),
              SizedBox(height: 200,),
              GestureDetector(
                onTap: (){},
                child: Container(  
                  width: double.infinity,
                  color: Colors.transparent,
                  child: Row(
                    children: [
                      Padding(padding: EdgeInsets.symmetric(vertical: 20),
                      child: Icon(
                        Icons.home,
                        color:selectedIndex==1?Colors.black:MyColor.iconGrayColor),
                      ),
                      Container(height: 40,width: 3,decoration: BoxDecoration(
                        color: selectedIndex==1?Colors.black:Colors.transparent,
                        borderRadius: BorderRadius.circular(5)
                      ),)
                    ],
                  ),
                ),
              )
            ],
          ), 
        ),
      ),
    );
  }
}