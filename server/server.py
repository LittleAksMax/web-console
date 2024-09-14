import asyncio
from websockets.asyncio.server import serve
import sys


async def handler(websocket):
    while True:
        msg = await websocket.recv()
        print(f"Server received: '{msg}'")

        if msg == "QUIT":
            await websocket.send("QUITTING")
            print("Quitting Connection")
            break

        await websocket.send("Pong")
        print(f"Message sent: Pong")

async def main():
    async with serve(handler, "0.0.0.0", 3000):
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())
