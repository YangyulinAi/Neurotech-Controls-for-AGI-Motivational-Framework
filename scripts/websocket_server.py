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

    async def handler(self, websocket, path):
        # 只接受 /ws 这个路径
        if path != "/ws":
            self.logger.warning(f"Rejected connection on path: {path}")
            await websocket.close(code=1008, reason="Invalid path")
            return

        # 正式接入
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.remote_address} (path={path})")
        try:
            await websocket.wait_closed()
        except Exception:
            self.logger.error("WebSocket handler exception", exc_info=True)
        finally:
            self.clients.remove(websocket)
            self.logger.info(f"Client disconnected: {websocket.remote_address}")

    async def broadcast(self, message: dict):
        data = json.dumps(message)
        if not self.clients:
            return
        tasks = [asyncio.create_task(ws.send(data)) for ws in self.clients]
        done, pending = await asyncio.wait(
            tasks, return_when=asyncio.ALL_COMPLETED
        )

    # 在 WebSocketServer 类中添加这个方法：
    async def send_to_frontend(self, data: dict):
        """发送数据到前端仪表板"""
        try:
            frontend_data = {
                'type': 'bci_data',
                'payload': {
                    'valence': data['valence'],
                    'arousal': data['arousal'],
                    'sessionId': data.get('version', 'live_session')
                }
            }

            # 连接到前端WebSocket服务器
            uri = "ws://localhost:5000/ws"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(frontend_data))

        except Exception as e:
            self.logger.error(f"Failed to send data to frontend: {e}")
    def start(self):
        # 不要传 path，下面的 handler 会自己过滤
        return websockets.serve(
            self.handler,
            self.host,
            self.port
        )
