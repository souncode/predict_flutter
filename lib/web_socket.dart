import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(title: 'WebSocket Test', home: WebSocketPage());
  }
}

String connectionStatus = "🔄 Connecting...";

class WebSocketPage extends StatefulWidget {
  @override
  State<WebSocketPage> createState() => _WebSocketPageState();
}

class _WebSocketPageState extends State<WebSocketPage> {
  late WebSocketChannel channel;
  final TextEditingController controller = TextEditingController();
  String receivedMessage = '';

  @override
  void initState() {
    super.initState();

    try {
      channel = WebSocketChannel.connect(
        Uri.parse('ws://172.20.10.3:8000'), // Đổi IP đúng
      );

      connectionStatus = "✅ Connected to server";

      channel.stream.listen(
        (message) {
          print("📥 [RECV] $message");
          setState(() {
            receivedMessage = message;
          });
        },
        onDone: () {
          print("❌ Disconnected");
          setState(() {
            connectionStatus = "❌ Disconnected from server";
          });
        },
        onError: (error) {
          print("⚠️ Error: $error");
          setState(() {
            connectionStatus = "⚠️ Connection error";
          });
        },
      );
    } catch (e) {
      setState(() {
        connectionStatus = "❌ Connection failed";
      });
    }
  }

  void sendMessage() {
    final msg = controller.text;
    print("📤 [SEND to Server] $msg");
    channel.sink.add(msg);
  }

  @override
  void dispose() {
    channel.sink.close();
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("WebSocket Test")),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(connectionStatus, style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 10),
            TextField(controller: controller),
            ElevatedButton(onPressed: sendMessage, child: const Text("Send")),
            const SizedBox(height: 20),
            Text("📥 From Server:\n$receivedMessage"),
          ],
        ),
      ),
    );
  }
}
