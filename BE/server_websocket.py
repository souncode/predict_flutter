import asyncio
import websockets

async def handler(websocket):  # 🔧 Sửa ở đây: thêm 'path'
    print("✅ Flutter connected")
    try:
        async for message in websocket:
            print(f"📩 [RECV] {message}")
            response = f"Server received: {message}"
            await websocket.send(response)
            print(f"📤 [SEND] {response}")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Connection closed")

async def main():
    print("🚀 Starting WebSocket server on ws://0.0.0.0:8765 ...")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("🟢 Server ready and waiting for connections...")
        await asyncio.Future()

asyncio.run(main())
