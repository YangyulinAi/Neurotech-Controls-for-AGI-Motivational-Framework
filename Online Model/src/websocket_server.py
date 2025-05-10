# online/src/websocket_server.py
import asyncio
import websockets
import json
import logging

class WebSocketServer:
    def __init__(self, host, port, logger=None):
        self.host = host
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        self.clients = set()

    async def handler(self, websocket):
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.remote_address}")
        try:
            await websocket.wait_closed()
        except Exception as e:
            self.logger.error("WebSocket handler exception", exc_info=True)
        finally:
            self.clients.remove(websocket)
            self.logger.info(f"Client disconnected: {websocket.remote_address}")

    async def broadcast(self, message: dict):
        data = json.dumps(message)
        n = len(self.clients)
        if n == 0:
            #self.logger.warning("[Broadcast] no clients connected")
            return

        #self.logger.debug(f"[Broadcast] sending to {n} clients: {data}")
        tasks = [asyncio.create_task(ws.send(data)) for ws in self.clients]
        done, pending = await asyncio.wait(
            tasks, return_when=asyncio.ALL_COMPLETED
        )
        #self.logger.debug(f"[Broadcast] completed → success={len(done)} fail={len(pending)}")


    def start(self):
        return websockets.serve(self.handler, self.host, self.port)