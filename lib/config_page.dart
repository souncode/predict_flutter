import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:predict_ai/constant/constant.dart';

class ConfigPage extends StatefulWidget {
  const ConfigPage({super.key});

  @override
  State<ConfigPage> createState() => _ConfigPageState();
}

class _ConfigPageState extends State<ConfigPage> {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        SizedBox(
          child: Column(
            children: [
              SizedBox(width: 200,),
              Text("Config",
              style: GoogleFonts.alfaSlabOne(
                fontSize: 30,
          
                height: 1.3,
                color: MyColor.primaryColor
              ),),
              Text("Camera",
              style: TextStyle(
                fontSize: 16,
                height: 1.3,
                color: MyColor.primaryColor
              ),)
            ],
          ),
        ),
        Expanded(
          
          child: TextField(
            
          decoration: InputDecoration(
             prefix: Icon(Icons.search,color: Colors.black,),
            hintText: "search",
            hintStyle: TextStyle(
            ),
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.only(left: 40,right: 5),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(30),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(30),
            ),
          )
          ),
        )
      ],
    );
  }
}
