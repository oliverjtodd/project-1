from fastapi import WebSocket, status
from Libs.Schema import WebsocketBody


class ConnectionManager:
    def __init__(self):
        self.ws_connected_keys = []
        self.ws_clients = []
        self.ws_connections = {}

    def get_ws_clients(self):
        return self.ws_clients

    async def accept_socket(self, websocket: WebSocket):
        await websocket.accept()

    async def close_socket(self, websocket: WebSocket, _type: int):
        match _type:
            case 1000:
                stat = status.WS_1000_NORMAL_CLOSURE
            case 1005:
                stat = status.WS_1005_ABNORMAL_CLOSURE
            case 1008:
                stat = status.WS_1008_POLICY_VIOLATION
        await websocket.close(code=stat)

    def append_socket(self, websocket: WebSocket):
        self.ws_clients.append(websocket)

    def remove_socket(self, websocket: WebSocket):
        self.ws_clients.remove(websocket)

    def remove_key(self, websocket: WebsocketBody):
        self.ws_connected_keys.remove(websocket.Authkey)

    def add_key(self, websocket: WebsocketBody):
        self.ws_connected_keys.append(websocket.Authkey)

    async def send_payload(self, data: dict, websocket: WebSocket):
        await websocket.send_json(data)

    def add_connection(self, discord_id: int, websocket: WebsocketBody):
        self.ws_connections[discord_id] = {
            "WebSocketID": websocket.ID,
            "AuthKey": websocket.Authkey,
            "DiscordName": websocket.Name,
            "DiscordID": websocket.DID,
            "HWID": websocket.HWID,
            "WorldID": None,
            "LobbyPlayers": [],
            "UserID": None,
            "AccessType": websocket.SocketType,
            "UserHash": websocket.UserHash,
        }

    def remove_connection(self, discord_id: int):
        del self.ws_connections[discord_id]
