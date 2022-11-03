import UnityPy
import copy
import asyncio
from Core.BaseVars import baseVars
from Libs.Webhooks import Webhook
from aioify import aioify
from Libs.Logger import Logger
from Libs.Utils import Utils, sanitise_input
from Libs.Shazam.SongFinder import ShazamUtil
from Libs.DataModel import AccessRoles, WebsocketBody
from youtubesearchpython.__future__ import VideosSearch


class SocketFuncs:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.avatars = self.db["Avatars"]
        self.tags = self.db["Tags"]
        self.avatar_search_log = self.db["AvatarSearchLog"]
        self.blacklisted_authors = self.db["BlacklistedAuthors"]
        self.archive_avatars = self.db["ArchiveAvatars"]
        self.BaseVars = BaseVars
        self.utils = Utils(BaseVars)
        self.log = Logger()
        self.shazam_u = aioify(obj=ShazamUtil(self.log), name="shazam")
        self.webhook = Webhook(BaseVars)

    # async def getAudioClip(self, url: str, name):
    #    self.log.info("Downloading asset bundle")
    #    bundle = await self.BaseVars.vrcapi.request(url)
    #    self.log.info("Done")
    #    env = UnityPy.load(bundle)
    #    for obj in env.objects:
    #        if obj.type.name == "AudioClip":
    #            audio = obj.read()
    #            if name == audio.name:
    #                for name, data in audio.samples.items():
    #                    return data

    async def fetchTags(self, websocket: WebsocketBody):
        tags = []
        async for x in self.tags.find({}):
            temp_x = x
            del temp_x["_id"]
            tags.append(temp_x)

        await self.BaseVars.ConnectionManager.send_payload(
            {"payload": {"type": "FetchedTags", "data": {"tags": tags}}}, websocket
        )

    # async def youtubeFunc(self, websocket, _):
    #    result  = VideosSearch(_['payload']['data']['query'], limit = 50)
    #    result = await result.next()
    #    await self.BaseVars.ConnectionManager.send_payload(
    #        {
    #            "payload" : {
    #                "type" : "YoutubeResult",
    #                "data" : result
    #        }
    #    }, websocket)

    # async def shazamFunc(self, websocket, _):
    #    url = _['payload']['data']['assetbundleurl']
    #    name = _['payload']['data']['clipname']
    #    audiodata = await self.getAudioClip(url, name)
    #    res = await self.shazam_u.song_name(audiodata)
    #    payload = {
    #            "payload" : {
    #                "type" : "ShazamResult",
    #                "data" : None
    #            }
    #        }
    #    if res['short_result'] != None:
    #        payload['payload']['data'] = {
    #            "song_name" : res['short_result']['name'],
    #            "song_artist" : res['short_result']['artist'],
    #            "song_covers" : res['short_result']['images'],
    #            "song_full_title" : res['short_result']['full_title'],
    #            "song_youtube_url" : res['short_result']['youtube_results']['result'][0]['link']
    #        }
    #        await self.BaseVars.ConnectionManager.send_payload(payload, websocket)
    #    else:
    #        payload['payload']['data'] = "No song found"
    #        await self.BaseVars.ConnectionManager.send_payload(payload, websocket)

    async def addAvatar(self, ws: WebsocketBody, _: dict):
        await self.utils.addAvatar(_, ws, websocket=True)

    async def avatarSearch(self, ws: WebsocketBody, _: dict):
        query = str(_["payload"]["data"]["query"])
        res = await self.utils.Search(
            decider=ws,
            search_type=_["payload"]["data"]["searchtype"],
            query=query.strip().replace("[", "").replace("]", ""),
            fields=_["payload"]["data"]["fields"],
            websocket=True,
        )
        payload = {"payload": {"type": "SearchResult", "data": res}}
        await self.BaseVars.ConnectionManager.send_payload(payload, ws)

    async def remoteRefreshTags(self, clients: list, _: dict):
        connections = copy.deepcopy(self.BaseVars.ConnectionManager.ws_connections)
        for user in clients:
            for user_data in connections:
                if user.ID == connections[user_data]["WebSocketID"]:
                    if (
                        connections[user_data]["WorldID"]
                        == _["payload"]["data"]["world_id"]
                    ):
                        await self.fetchTags(user)

    async def remoteCrashGame(self, websocket: WebsocketBody, clients: list, _: dict):
        for client in clients:
            if client.ID == _["payload"]["data"]["websocket_id"]:
                await self.BaseVars.ConnectionManager.send_payload(
                    {"payload": {"type": "CrashGame"}}, client
                )

    async def findBlazeUser(self, websocket: WebsocketBody, _: dict):
        connections = copy.deepcopy(self.BaseVars.ConnectionManager.ws_connections)
        users = []
        for user in connections:
            if (
                connections[user]["WorldID"] == _["payload"]["data"]["world_id"]
                and websocket.ID != connections[user]["WebSocketID"]
            ):
                users.append(
                    {
                        "UserID": connections[user]["UserID"],
                        "AccessType": connections[user]["AccessType"],
                    }
                )
        results = users if len(users) != 0 else None
        payload = {"payload": {"type": "FoundBlazeUsers", "data": {"Users": results}}}
        await self.BaseVars.ConnectionManager.send_payload(payload, websocket)

    async def fetchOnline(self, websocket: WebsocketBody):
        connections = copy.deepcopy(self.BaseVars.ConnectionManager.ws_connections)
        match websocket.SocketType:
            case valid if valid in [
                AccessRoles.DEVELOPER.value,
                AccessRoles.STAFF.value,
            ]:
                payload = {
                    "payload": {"type": "SendOnline", "data": {"users": connections}}
                }
            case AccessRoles.USER.value:
                for key in connections.keys():
                    try:
                        del connections[key]["AuthKey"]
                    except:
                        pass
                    try:
                        del connections[key]["HWID"]
                    except:
                        pass
                    try:
                        del connections[key]["WorldID"]
                    except:
                        pass
                    try:
                        del connections[key]["UserID"]
                    except:
                        pass
            case _:
                connections = 0
        payload = {"payload": {"type": "SendOnline", "data": {"users": connections}}}
        await self.BaseVars.ConnectionManager.send_payload(payload, websocket)

    async def currentUser(self, websocket: WebsocketBody):
        fetch = await self.users.find_one({"_id": websocket.Authkey})
        match fetch:
            case None:
                user = "No user by that key"
            case _:
                user = fetch
                del user["ExtensionAccess"]
                del user["Favs"]
        await self.BaseVars.ConnectionManager.send_payload(
            {"payload": {"type": "ReceivedUserInfo", "data": user}}, websocket
        )

    async def command(self, _: dict, clients: list, websocket: WebsocketBody):
        match _["payload"]["type"]:
            case "MessageAll":
                command = {
                    "devname": websocket.Name,
                    "message": _["payload"]["data"]["message"],
                    "message_type": _["payload"]["data"]["message_type"],
                }
                payload = {"payload": {"type": _["payload"]["type"], "data": command}}
                await asyncio.wait([ws.send_json(payload) for ws in clients])
                await self.webhook.websocket_messageall_payload(
                    "MessageAll", clients, websocket.Name, _["payload"]
                )
                await self.BaseVars.ConnectionManager.send_payload(
                    {
                        "payload": {
                            "type": "ReturnCommandExecute",
                            "data": f"Message was sent to {len(clients)} connected clients",
                        }
                    },
                    websocket,
                )
