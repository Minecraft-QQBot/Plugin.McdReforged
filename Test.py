import websockets

import asyncio
from threading import Thread


async def client():
    uri = "ws://localhost:25565/ws"
    async with websockets.connect(uri, extra_headers={"Authorization": "Bearer <token>"}) as websocket:
        async for message in websocket:
            print(message)
        print("Connection closed")


async def server():
    async def handler(websocket):
        for i in range(10):
            await websocket.send(f"Hello {i}")
            await asyncio.sleep(1)

    server = await websockets.serve(handler, "localhost", 25565)
    await server.wait_closed()


class TestThread(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        self.loop = asyncio.new_event_loop()
        self.loop.create_task(server())
        self.loop.create_task(client())
        self.loop.run_forever()


if __name__ == "__main__":
    t = TestThread()
    t.start()
    t.join()
