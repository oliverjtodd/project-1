import json
import asyncio
import traceback
import bson
import re
import sys
import random
import copy
import base64
from fastapi import FastAPI, Request, Depends, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect
from Libs.DataModel import AccessRoles
from Libs.HttpResponseHandler import Handler
from Libs.Tasks import TaskAPI
from Libs.Webhooks import Webhook
from Libs.Auth import Auth
from Libs.Utils import Utils, sanitise_input
from Libs.Websocket import SocketFuncs
from Libs.Moderation import Moderation
from Libs.Blacklist import Blacklist
from Libs.Registry import Registry
from Libs.Tags import Tags
from Libs.CaptchaSolver import CaptchaSolver
from Libs.Schema import APISchema, WebsocketBody
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
from Core.BaseVars import baseVars
import Core.CustomExceptions

sys.setrecursionlimit(100000)

base_router = InferringRouter()
testing_router = InferringRouter()
user_router = InferringRouter()
tags_router = InferringRouter()
avatar_router = InferringRouter()
websocket_router = InferringRouter()
admin_router = InferringRouter()

BaseVars = baseVars()
tasks = TaskAPI(BaseVars)

app = FastAPI(
    openapi_tags=BaseVars.FASTAPI_CONFIG["openapi_tags"],
    title=BaseVars.FASTAPI_CONFIG["title"],
    description=BaseVars.FASTAPI_CONFIG["description"],
    version=BaseVars.FASTAPI_CONFIG["version"],
    openapi_url=BaseVars.FASTAPI_CONFIG["openapi_url"],
    docs_url=BaseVars.FASTAPI_CONFIG["docs_url"],
    contact=BaseVars.FASTAPI_CONFIG["contact"],
    debug=False
    
)
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def start_up():
    BaseVars.dynamic_lists["systemtasks"] = []
    BaseVars.dynamic_lists["eventloop"] = asyncio.get_event_loop()
    name = BaseVars.db["BlazesMod"]
    list_names = await name.list_collection_names()
    BaseVars.log.info("===== [ Current collections in database ] =====")
    for x in list_names:
        BaseVars.log.info(f"Document -> {x}")
    BaseVars.log.info("===============================================")
    BaseVars.log.info("Executing background tasks")
    task_list = [tasks.avatarStats(), tasks.regularLists(), tasks.lateLists()]
    for task in task_list:
        t = BaseVars.dynamic_lists["eventloop"].create_task(task)
        BaseVars.log.success(f"Started task method: {task.__name__}")
        BaseVars.dynamic_lists["systemtasks"].append(t)


@app.middleware(BaseVars.MIDDLE_WARE)
async def log_request(request: Request, call_next):
    response: Request = await call_next(request)
    BaseVars.dynamic_lists["eventloop"].create_task(
        Webhook(BaseVars).request_payload(request)
    )
    response.headers["X-Run-By"] = "BlazeModSystems"
    response.headers["X-What-Is-This"] = random.choice(BaseVars.RANDO_HEADERS)
    return response


@cbv(admin_router)
class APIAdmin:
    def __init__(self):
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.authenticator = Auth(BaseVars)

    @admin_router.get("/v3/admin/update")
    async def admin_actions(self, request: Request):
        #authCheck = await self.authenticator.auth(request=request)
        #match authCheck["Validation"]:
        #    case valid if valid == True and authCheck[
        #        "AccessType"
        #    ] == AccessRoles.DEVELOPER.value:
        #        pass
        #    case "BANNED":
        #        return self.responsehandler.Ban.ban(authCheck)
        #    case "NO-HEADERS":
        #        return self.responsehandler.Default.noheaders()
        #    case "INVALID-KEY-FORM":
        #        return self.responsehandler.Default.invalidkeyform()
        #    case _:
        #        return self.responsehandler.Default.unauthed()
        
        data = await request.json()

@app.exception_handler(Exception)
async def api_error_handler(request: Request, exec_: Exception):
    await Webhook(BaseVars).traceback_payload(traceback.format_exc())
    _handler = Handler()
    print(isinstance(exec_, Core.CustomExceptions.Auth.WrongHWID))
    match (type(exec_),):
        case (json.decoder.JSONDecodeError,): return _handler.Default.invaliddata() if len(re.findall(r"Expecting value:", str(exec_.args[0]))) == 0 else _handler.Default.nodata()
        case (KeyError,): return _handler.Default.incorrectdata(exec_)
        case _: return _handler.Default.error(str(exec_))
    #return Handler().Default.error(traceback.format_exc())

@cbv(testing_router)
class APITests:
    def __init__(self):
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.avatars = self.db["Avatars"]
        self.tags = self.db["Tags"]
        self.avatar_search_log = self.db["AvatarSearchLog"]
        self.blacklisted_authors = self.db["BlacklistedAuthors"]
        self.archive_avatars = self.db["ArchiveAvatars"]
        self.avatars_testing = self.db["AvatarsTesting"]
        self.avatar_blacklist = self.db["AvatarBlacklist"]
        self.utils = Utils(BaseVars)
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.socketfuncs = SocketFuncs(BaseVars)
        self.authenticator = Auth(BaseVars)
        self.moderation = Moderation(BaseVars)
        self.blacklist = Blacklist(BaseVars)
        self.registry = Registry(BaseVars)
        self.captcha_ = CaptchaSolver()

    @testing_router.post("/captcha")
    async def captchaSend(self, request: Request):
        try:
            data = await request.json()
        except Core.CustomExceptions.NoData:
            return self.responsehandler.Default.nodata()

        return await self.captcha_.send_data(data["data"])

    @testing_router.get("/captcha")
    async def captchaFetch(self, captchaid: int):
        return await self.captcha_.receive_data(captchaid)

    @testing_router.get("/find")
    async def test(self, type: str, name: str, access: int):
        if access == 17382:
            match type:
                case "avatar":
                    find = "AvatarName"
                case "author":
                    find = "AuthorName"
                case "authorid":
                    find = "AuthorID"
                case _:
                    find = "AvatarName"
            e = []
            body = ""
            async for x in self.avatars.find(
                {find: {"$regex": sanitise_input(name)}}
            ):
                e.append(x["AvatarName"])
                body += f'<div><p>Avatar Name: {x["AvatarName"]}</p><p>Avatar URL: {x["AssetURL"]}</p><p>Avatar ID: {x["_id"]}</p><p>Avatar Release Status: {x["ReleaseStatus"]}</p><p>Avatar Author: {x["AuthorName"]}</p><p>Author ID: {x["AuthorID"]}</p><img src={x["ImageURL"]} width="500" height="400"/></div><hr>\n'

            res = f"""
                <html>
                    <head>
                        <title>Test</title>
                    </head>
                    <body>
                    {body}
                    </body>
                </html>
            """
            return HTMLResponse(content=res, status_code=200)

    @testing_router.get("/cd179508-3489-494d-893e-38c4fb827415")
    async def test1(
        self, search: str = "", authorId: str = "", avatarId: str = "", n: int = 0
    ):
        try:
            if len(search) != 0:
                if re.match(
                    r"usr_[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
                    search.lower(),
                ):
                    find = "AuthorID"
                    query = search
                elif re.match(
                    r"avtr_[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
                    search.lower(),
                ):
                    find = "_id"
                    query = search
                else:
                    find = "AvatarName"
                    query = search
            elif len(authorId) != 0:
                if re.match(
                    r"usr_[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
                    authorId,
                ):
                    find = "AuthorID"
                    query = authorId
            elif len(avatarId) != 0:
                if re.match(
                    r"avtr_[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
                    avatarId,
                ):
                    find = "_id"
                    query = avatarId
            avis = []
            async for x in self.avatars.find(
                {find: {"$regex": re.compile(sanitise_input(query), re.IGNORECASE)}}
            ):
                a = {
                    "id": x["_id"],
                    "name": x["AvatarName"],
                    "authorId": x["AuthorID"],
                    "authorName": x["AuthorName"],
                    "description": x["Description"],
                    "imageUrl": x["ImageURL"],
                    "thumbnailImageUrl": x["ThumbnailImageURL"],
                    "releaseStatus": x["ReleaseStatus"],
                }
                avis.append(a)
            return self.responsehandler.globalresponse(avis, 200)
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())


@cbv(base_router)
class APIBase:
    def __init__(self):
        self.db = BaseVars.db["BlazesMod"]
        self.avatar_blacklist = self.db["AvatarBlacklist"]
        self.ascii = BaseVars.CONFIG_DATA["data"][1]["ascii_art"]
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.authenticator = Auth(BaseVars)
    
    
    @base_router.get("/v3/config")
    async def get_config(self):
        config = {
            "blacklist": BaseVars.dynamic_lists["aviblacklist"],
            "loaderversion": BaseVars.LOADER_VERSION,
            "clientversion": BaseVars.CLIENT_VERSION,
        }
        with open("config.c.json", "r", encoding="utf-8") as res:
            res: dict = json.load(res)

        config = {**config, **res}
        return self.responsehandler.globalresponse(config, 200)

    @base_router.get("/")
    def home(self):
        out = random.choice(self.ascii)
        return self.responsehandler.globalresponse(out, 200)


@cbv(websocket_router)
class APIWebsocket:
    def __init__(self):
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.tags = Tags(BaseVars)
        self.utils = Utils(BaseVars)
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.socketfuncs = SocketFuncs(BaseVars)
        self.authenticator = Auth(BaseVars)

    @websocket_router.get("/v3/ws/connected")
    async def getusers(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            connections = copy.deepcopy(BaseVars.ConnectionManager.ws_connections)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                    AccessRoles.USER.value,
                ]:
                    match authCheck["AccessType"]:
                        case valid if valid == authCheck["AccessType"] in [
                            AccessRoles.DEVELOPER.value,
                            AccessRoles.STAFF.value,
                        ]:
                            pass
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
                                    del connections[key]["UserID"]
                                except:
                                    pass
                                try:
                                    del connections[key]["WorldID"]
                                except:
                                    pass
                    return self.responsehandler.Admin.onlineusers(connections)
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @websocket_router.post("/v3/ws/command")
    async def command(
        self,
        request: Request,
        clients=Depends(BaseVars.ConnectionManager.get_ws_clients),
    ):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            if len(clients) == 0:
                return self.responsehandler.Admin.noonlineusers()

            developer = authCheck["DiscordName"]
            command_type = data["data"]["command_type"]

            match command_type:
                case "MessageAll":
                    command = {
                        "devname": developer,
                        "message": data["data"]["message"],
                        "message_type": data["data"]["message_type"],
                    }
                    payload = {"payload": {"type": command_type, "data": command}}
                    await asyncio.wait([ws.send_json(payload) for ws in clients])
                    await self.webhook.websocket_messageall_payload(
                        command_type, clients, developer, data
                    )
                    return self.responsehandler.Admin.Command.broadcast(len(clients))

                case "MessageUser":
                    command = {
                        "devname": developer,
                        "message": data["data"]["message"],
                        "message_type": data["data"]["message_type"],
                    }
                    payload = {"payload": {"type": command_type, "data": command}}
                    for ws in clients:
                        if ws.ID == data["data"]["websocket_id"]:
                            await BaseVars.ConnectionManager.send_payload(payload, ws)
                            await self.webhook.websocket_command_payload(
                                command_type, ws, developer
                            )
                            return JSONResponse(
                                content={
                                    "response": f"Message was sent to {ws.Name} by developer {developer}"
                                },
                                status_code=200,
                            )
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @websocket_router.websocket("/v3/connect/{authkey}/{userhash}")
    async def websocket_endpoint(
        self,
        websocket: WebSocket,
        authkey: str,
        userhash: str,
        clients: list = Depends(BaseVars.ConnectionManager.get_ws_clients),
    ):
        try:
            if (
                re.match(
                    r"BM_[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}_[a-f0-9]{32}",
                    authkey,
                )
                is None
            ):
                await BaseVars.ConnectionManager.accept_socket(websocket)
                await BaseVars.ConnectionManager.send_payload(
                    {"payload": {"data": "Invalid key supplied, socket closing"}},
                    websocket,
                )
                await BaseVars.ConnectionManager.close_socket(websocket, 1008)
                return

            if re.match(r"[a-f0-9]{32}", userhash) is None:
                await BaseVars.ConnectionManager.accept_socket(websocket)
                await BaseVars.ConnectionManager.send_payload(
                    {"payload": {"data": "Invalid hash supplied, socket closing"}},
                    websocket,
                )
                await BaseVars.ConnectionManager.close_socket(websocket, 1008)
                return

            user = await self.users.find_one({"_id": sanitise_input(authkey)})
            if user == None:
                await BaseVars.ConnectionManager.accept_socket(websocket)
                await BaseVars.ConnectionManager.send_payload(
                    {"payload": {"data": "No user found by this key, socket closing"}},
                    websocket,
                )
                await BaseVars.ConnectionManager.close_socket(websocket, 1008)
                return

            discord_id = user["DiscordID"]
            check = await self.authenticator.websocket_auth(
                user=user,
                websocket=websocket,
                discord_id=discord_id,
                ConnectionManager=BaseVars.ConnectionManager,
                userhash=userhash,
                clients=clients,
            )
            try:

                while True:
                    try:
                        _ = await websocket.receive_json()
                        BaseVars.log.success(
                            f"{websocket.Name} sent payload {_['payload']['type']}"
                        )
                    except Exception as e:
                        match isinstance(e, WebSocketDisconnect):
                            case True:
                                raise WebSocketDisconnect
                            case _:
                                await BaseVars.ConnectionManager.send_payload(
                                    {"payload": {"data": "Invalid payload"}}, websocket
                                )
                                continue
                    try:
                        match _["payload"]["type"]:
                            case valid if valid == "VRChatAPIInfo" and check[
                                "AccessLevel"
                            ] in [
                                AccessRoles.DEVELOPER.value,
                                AccessRoles.STAFF.value,
                                AccessRoles.USER.value,
                            ]:
                                try:
                                    BaseVars.ConnectionManager.ws_connections[
                                        discord_id
                                    ]["WorldID"] = _["payload"]["data"]["world_id"]
                                    BaseVars.ConnectionManager.ws_connections[
                                        discord_id
                                    ]["UserID"] = _["payload"]["data"]["user_id"]
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "FetchUserInfo" and check[
                                "AccessLevel"
                            ] in [
                                AccessRoles.DEVELOPER.value,
                                AccessRoles.STAFF.value,
                                AccessRoles.USER.value,
                            ]:
                                try:
                                    await self.socketfuncs.currentUser(websocket)
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            # case valid if valid == "ShazamFunc" and check['AccessLevel'] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value, AccessRoles.USER.value]:
                            #    try:
                            #        asyncio.create_task(self.socketfuncs.shazamFunc(websocket, _))
                            #    except Exception as e:
                            #        await self.webhook.traceback_payload(traceback.format_exc())
                            #        raise KeyError(e)

                            #case valid if valid == "FetchAudioClipFromAvatar" and check[
                            #    "AccessLevel"
                            #] in [
                            #    AccessRoles.DEVELOPER.value,
                            #    AccessRoles.STAFF.value,
                            #    AccessRoles.USER.value,
                            #]:
                            #    try:
                            #        data = await self.socketfuncs.getAudioClip(
                            #            _["payload"]["data"]["assetbundleurl"],
                            #            _["payload"]["data"]["clipname"],
                            #        )
                            #        await BaseVars.ConnectionManager.send_payload(
                            #            {
                            #                "payload": {
                            #                    "type": "ResultAudioClipFromAvatar",
                            #                    "data": {
                            #                        "audiodata": str(
                            #                            base64.b64encode(data).decode(
                            #                                "utf-8"
                            #                            )
                            #                        )
                            #                    },
                            #                }
                            #            },
                            #            websocket,
                            #       )
                            #    except Exception as e:
                            #        await self.webhook.traceback_payload(
                            #            traceback.format_exc()
                            #        )
                            #        raise KeyError(e)

                            # case valid if valid == "YoutubeFunc" and check['AccessLevel'] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value, AccessRoles.USER.value]:
                            #    try:
                            #        await self.socketfuncs.youtubeFunc(websocket, _)
                            #    except Exception as e:
                            #        await self.webhook.traceback_payload(traceback.format_exc())
                            #        raise KeyError(e)

                            case valid if valid == "FindBlazeUser" and check[
                                "AccessLevel"
                            ] in [
                                AccessRoles.DEVELOPER.value,
                                AccessRoles.STAFF.value,
                                AccessRoles.USER.value,
                            ]:
                                try:
                                    await self.socketfuncs.findBlazeUser(websocket, _)
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "FetchOnline" and check[
                                "AccessLevel"
                            ] in [
                                AccessRoles.DEVELOPER.value,
                                AccessRoles.STAFF.value,
                                AccessRoles.USER.value,
                            ]:
                                try:
                                    await self.socketfuncs.fetchOnline(websocket)
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "AvatarSearch" and check[
                                "AccessLevel"
                            ] in [role.value for role in AccessRoles]:
                                try:
                                    await self.socketfuncs.avatarSearch(websocket, _)
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "AvatarAdd" and check[
                                "AccessLevel"
                            ] in [
                                AccessRoles.DEVELOPER.value,
                                AccessRoles.STAFF.value,
                                AccessRoles.USER.value,
                            ]:
                                try:
                                    await self.utils.addAvatar(_, websocket, True)
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case "FetchAvatarDBStats":
                                try:
                                    await BaseVars.ConnectionManager.send_payload(
                                        {
                                            "payload": {
                                                "type": "AvatarDBStats",
                                                "data": BaseVars.dynamic_lists[
                                                    "avistats"
                                                ],
                                            }
                                        },
                                        websocket,
                                    )
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "FetchTags" and check[
                                "AccessLevel"
                            ] in [
                                AccessRoles.DEVELOPER.value,
                                AccessRoles.STAFF.value,
                                AccessRoles.USER.value,
                            ]:
                                try:
                                    await self.tags.fetchTags(
                                        {
                                            "Manager": BaseVars.ConnectionManager,
                                            "Socket": websocket,
                                        }
                                    )
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "AddTag" and check[
                                "AccessLevel"
                            ] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value]:
                                try:
                                    await self.tags.addTag(
                                        _["payload"]["data"],
                                        {
                                            "Manager": BaseVars.ConnectionManager,
                                            "Socket": websocket,
                                        },
                                    )
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "RemoveTag" and check[
                                "AccessLevel"
                            ] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value]:
                                try:
                                    await self.tags.removeTag(
                                        _["payload"]["data"],
                                        {
                                            "Manager": BaseVars.ConnectionManager,
                                            "Socket": websocket,
                                        },
                                    )
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "UpdateTag" and check[
                                "AccessLevel"
                            ] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value]:
                                try:
                                    await self.tags.updateTag(
                                        _["payload"]["data"],
                                        {
                                            "Manager": BaseVars.ConnectionManager,
                                            "Socket": websocket,
                                        },
                                    )
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "FetchUserTag" and check[
                                "AccessLevel"
                            ] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value]:
                                try:
                                    await self.tags.fetchTag(
                                        _["payload"]["data"],
                                        {
                                            "Manager": BaseVars.ConnectionManager,
                                            "Socket": websocket,
                                        },
                                    )
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "MessageAll" and check[
                                "AccessLevel"
                            ] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value]:
                                try:
                                    await self.socketfuncs.command(
                                        _, clients, websocket
                                    )
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "RemoteRefreshTags" and check[
                                "AccessLevel"
                            ] in [AccessRoles.DEVELOPER.value, AccessRoles.STAFF.value]:
                                try:
                                    await self.socketfuncs.remoteRefreshTags(clients, _)
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case valid if valid == "SendLobbyPlayers" and check[
                                "AccessLevel"
                            ] in [
                                AccessRoles.DEVELOPER.value,
                                AccessRoles.STAFF.value,
                                AccessRoles.USER.value,
                            ]:
                                try:
                                    websocket.LobbyPlayers = _["payload"]["data"][
                                        "players"
                                    ]
                                except Exception as e:
                                    await self.webhook.traceback_payload(
                                        traceback.format_exc()
                                    )
                                    raise KeyError(e)

                            case _:
                                await BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "AccessDenied",
                                            "data": "You are not permitted to use this payload or the payload does not exist",
                                        }
                                    },
                                    websocket,
                                )

                    except KeyError as e:
                        await BaseVars.ConnectionManager.send_payload(
                            {
                                "payload": {
                                    "type": "InternalError",
                                    "data": f"Error in payload execution: {e}",
                                }
                            },
                            websocket,
                        )

            except WebSocketDisconnect:
                BaseVars.log.success(f"Websocket Closed, awaiting information")

            finally:
                match check["Result"]:
                    case "IsBanned":
                        for client in clients:
                            if (
                                client.SocketType
                                in [
                                    AccessRoles.DEVELOPER.value,
                                    AccessRoles.STAFF.value,
                                ]
                                and client.Name != websocket.Name
                            ):
                                await BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "OnUserAttemptBanned",
                                            "data": {
                                                "name": websocket.Name,
                                                "level": websocket.SocketType,
                                            },
                                        }
                                    },
                                    client,
                                )
                        await BaseVars.ConnectionManager.accept_socket(websocket)
                        await BaseVars.ConnectionManager.send_payload(
                            {
                                "payload": {
                                    "type": "AccessDenied",
                                    "data": "Key is banned from using mod",
                                }
                            },
                            websocket,
                        )
                        await BaseVars.ConnectionManager.close_socket(websocket, 1008)
                        return

                    case "IsDuplicate":
                        for client in clients:
                            if (
                                client.SocketType
                                in [
                                    AccessRoles.DEVELOPER.value,
                                    AccessRoles.STAFF.value,
                                ]
                                and client.Name != websocket.Name
                            ):
                                await BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "OnUserAttemptDuplicate",
                                            "data": {
                                                "name": websocket.Name,
                                                "level": websocket.SocketType,
                                            },
                                        }
                                    },
                                    client,
                                )
                        await BaseVars.ConnectionManager.accept_socket(websocket)
                        await BaseVars.ConnectionManager.send_payload(
                            {
                                "payload": {
                                    "type": "AccessDenied",
                                    "data": "Key is already connected",
                                }
                            },
                            websocket,
                        )
                        await BaseVars.ConnectionManager.close_socket(websocket, 1008)
                        return

                    case "IsUnAuthorised":
                        for client in clients:
                            if (
                                client.SocketType
                                in [
                                    AccessRoles.DEVELOPER.value,
                                    AccessRoles.STAFF.value,
                                ]
                                and client.Name != websocket.Name
                            ):
                                await BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "OnUserAttemptUnAuthorised",
                                            "data": {
                                                "name": websocket.Name,
                                                "level": websocket.SocketType,
                                            },
                                        }
                                    },
                                    client,
                                )
                        await BaseVars.ConnectionManager.accept_socket(websocket)
                        await BaseVars.ConnectionManager.send_payload(
                            {
                                "payload": {
                                    "type": "AccessDenied",
                                    "data": "Key is not authorised to use websocket",
                                }
                            },
                            websocket,
                        )
                        await BaseVars.ConnectionManager.close_socket(websocket, 1008)
                        return

                    case "IncorrectHash":
                        for client in clients:
                            if (
                                client.SocketType
                                in [
                                    AccessRoles.DEVELOPER.value,
                                    AccessRoles.STAFF.value,
                                ]
                                and client.Name != websocket.Name
                            ):
                                await BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "OnUserAttemptIncorrectHash",
                                            "data": {
                                                "name": websocket.Name,
                                                "level": websocket.SocketType,
                                            },
                                        }
                                    },
                                    client,
                                )
                        await BaseVars.ConnectionManager.accept_socket(websocket)
                        await BaseVars.ConnectionManager.send_payload(
                            {
                                "payload": {
                                    "type": "AccessDenied",
                                    "data": "UserHash does not match key",
                                }
                            },
                            websocket,
                        )
                        await BaseVars.ConnectionManager.close_socket(websocket, 1008)
                        return

                    case _:
                        for client in clients:
                            if (
                                client.SocketType
                                in [
                                    AccessRoles.DEVELOPER.value,
                                    AccessRoles.STAFF.value,
                                ]
                                and client.Name != websocket.Name
                            ):
                                await BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "OnUserOffline",
                                            "data": {
                                                "name": websocket.Name,
                                                "level": websocket.SocketType,
                                            },
                                        }
                                    },
                                    client,
                                )
                        BaseVars.ConnectionManager.remove_key(websocket)
                        BaseVars.ConnectionManager.remove_socket(websocket)
                        BaseVars.ConnectionManager.remove_connection(discord_id)
                        await self.webhook.websocket_disconnect_payload(websocket)
                        BaseVars.log.info(
                            f"{websocket.Name} has disconnected from the websocket"
                        )
        except:
            BaseVars.log.error(traceback.format_exc())


@cbv(tags_router)
class APITags:
    def __init__(self):
        self.db = BaseVars.db["BlazesMod"]
        self.tags = Tags(BaseVars)
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.authenticator = Auth(BaseVars)

    @tags_router.get("/v3/user/tags")
    async def get_tags(
        self, request: Request, auth: str | bool = False, user: str | bool = False
    ):
        authCheck = await self.authenticator.auth(request=request, param=auth)
        match authCheck["Validation"]:
            case valid if valid == True and authCheck["AccessType"] in [
                AccessRoles.DEVELOPER.value,
                AccessRoles.STAFF.value,
                AccessRoles.SPECIAL.value,
                AccessRoles.USER.value,
            ]:
                match user:
                    case False:
                        return await self.tags.fetchTags()
                    case usr if isinstance(usr, str) is True:
                        return await self.tags.fetchTag(user)
            case "BANNED":
                return self.responsehandler.Ban.ban(authCheck)
            case "NO-HEADERS":
                return self.responsehandler.Default.noheaders()
            case "INVALID-KEY-FORM":
                return self.responsehandler.Default.invalidkeyform()
            case _:
                return self.responsehandler.Default.unauthed()

    @tags_router.post("/v3/user/tags")
    async def add_tag(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.tags.addTag(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @tags_router.put("/v3/user/tags")
    async def update_tag(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.tags.updateTag(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @tags_router.delete("/v3/user/tags")
    async def delete_tag(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    raise Core.CustomExceptions.Ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.tags.removeTag(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())


@cbv(avatar_router)
class APIAvatars:
    def __init__(self):
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.avatars = self.db["Avatars"]
        self.avatar_search_log = self.db["AvatarSearchLog"]
        self.blacklisted_authors = self.db["BlacklistedAuthors"]
        self.utils = Utils(BaseVars)
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.authenticator = Auth(BaseVars)
        self.blacklist = Blacklist(BaseVars)

    @avatar_router.put("/v3/avatar/blacklist")
    async def add_blacklist_avatar(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.blacklist.game_avatar_add(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.delete("/v3/avatar/blacklist")
    async def remove_blacklist_avatar(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.blacklist.game_avatar_remove(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.post("/v3/avatar/search/blacklist/avatar")
    async def search_blacklist_avatar_add(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.blacklist.search_avatar_add(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.delete("/v3/avatar/search/blacklist/avatar")
    async def search_blacklist_avatar_remove(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.blacklist.search_avatar_remove(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.post("/v3/avatar/search/blacklist/author")
    async def search_blacklist_author_add(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.blacklist.search_author_add(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.delete("/v3/avatar/search/blacklist/author")
    async def search_blacklist_author_remove(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.blacklist.search_author_remove(data["data"])
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.get("/v3/avatar/stats")
    async def stats(self):
        try:
            return JSONResponse(
                content=BaseVars.dynamic_lists["avistats"], status_code=200
            )
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.put(
        "/v3/avatar/add", response_model=APISchema.MainResponses.MainResponseNoData
    )
    async def add_avatar(
        self, avatar: APISchema.AvatarModel.AvatarOutput.AvatarBody, request: Request
    ):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    role.value for role in AccessRoles
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.utils.addAvatar(data["data"], authCheck)
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @avatar_router.post("/v3/avatar/search")
    # @limiter.limit("10/second")
    async def search(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case True:
                    pass
                case "BANNED":
                    raise Core.CustomExceptions.Ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            search_type = data["search"]["search_type"]
            return await self.utils.Search(
                decider=authCheck,
                search_type=search_type,
                query=data["search"]["search_query"],
                fields=data["search"]["fields"],
            )
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())


@cbv(user_router)
class APIUsers:
    def __init__(self):
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.utils = Utils(BaseVars)
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.authenticator = Auth(BaseVars)
        self.registry = Registry(BaseVars)
        self.moderation = Moderation(BaseVars)

    @user_router.post("/v3/user/key/info")
    async def key_info(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    role.value for role in AccessRoles
                ]:
                    result = await self.users.find_one({"_id": authCheck["AuthKey"]})
                    if result != None:
                        result["DiscordID"] = bson.Int64(result["DiscordID"])
                        r = result
                        del r["Favs"]
                        return JSONResponse(content={"response": r}, status_code=200)
                    else:
                        return JSONResponse(
                            content={"response": "No user by that key"}, status_code=404
                        )
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.delete("/v3/user/hwid")
    async def hwid_reset(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.registry.resetHWID(data["data"])

        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.post("/v3/user/key/info/{id}")
    async def key_info_by_did(self, request: Request, id: int):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()
            print(id)
            result = await self.users.find_one({"DiscordID": id})
            if result != None:
                result["DiscordID"] = bson.Int64(result["DiscordID"])
                return JSONResponse(content=result)
            else:
                return JSONResponse(
                    content={"response": "No user found by discord ID"}, status_code=404
                )
        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.post("/v3/user/register")
    async def register_user(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.registry.register(authCheck, data["data"])

        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.post("/v3/user/register/regen")
    async def regen_user(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            return await self.registry.regenUser(authCheck, data["data"])

        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.post("/v3/user/auth")
    async def client_auth(self, request: Request, release: str = "live"):
        try:

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            authCheck = await self.authenticator.auth(
                request=request, loader=True, data=data
            )

            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                    AccessRoles.USER.value,
                ]:
                    pass

                case "INVALID-HWID":
                    return self.responsehandler.Auth.authwronghwid()

                case "BANNED":
                    await self.webhook.ban_payload(authCheck)
                    return self.responsehandler.Auth.authbanned(authCheck)

                case "NO-HEADERS":
                    return self.responsehandler.Auth.authnoheaders()

                case "NO-VERSION":
                   return self.responsehandler.Auth.authnoversion()

                case "INVALID-USER-AGENT":
                    return self.responsehandler.Auth.authinvaliduseragent()

                case "INVALID-KEY-FORM":
                    return self.responsehandler.Auth.authinvalidkeyform()

                case "OUTDATED":
                    return self.responsehandler.Auth.authoutdated()

                case _:
                    await self.webhook.key_payload(authCheck)
                    return self.responsehandler.Auth.authunauthorised()

            match release:
                case "live":
                    modt = "Mod/Mod.dll"
                    rel = "Live"
                case "beta":
                    modt = "Mod/Beta.dll"
                    rel = "Beta"
                case "bepinex":
                    modt = "Mod/Bepinex.dll"
                    rel = "Beta"
                case _:
                    return self.responsehandler.Auth.authinvalidrelease()

            with open(modt, "rb") as x: mod = x.read()
            message = f"Authorization Passed - Release: {rel}"
            mod = base64.b64encode(mod)
            user = authCheck["DiscordName"]
            level = authCheck["AccessType"]
            theMod = str(bytes(mod).decode("utf-8"))
            await self.webhook.authpass_payload(authCheck, data)

            response_login = {
                "api_info": {
                    "Valid": True,
                },
                "response": {
                    "message": f"{message} - Welcome {user}",
                    "level": level,
                    "mod": theMod,
                    "hash": authCheck["UserHash"],
                },
            }
            return JSONResponse(content=response_login, status_code=200)

        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.delete("/v3/user/moderate")
    async def moderate_user_remove(self, request: Request):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()

            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            match data["data"]["action"]:
                case "unban":
                    return await self.moderation.unbanUser(data["data"])

        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.post("/v3/user/moderate")
    async def moderate_user_add(
        self,
        request: Request,
        clients=Depends(BaseVars.ConnectionManager.get_ws_clients),
    ):
        try:
            authCheck = await self.authenticator.auth(request=request)
            match authCheck["Validation"]:
                case valid if valid == True and authCheck["AccessType"] in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    pass
                case "BANNED":
                    return self.responsehandler.Ban.ban(authCheck)
                case "NO-HEADERS":
                    return self.responsehandler.Default.noheaders()
                case "INVALID-KEY-FORM":
                    return self.responsehandler.Default.invalidkeyform()
                case _:
                    return self.responsehandler.Default.unauthed()
            try:
                data = await request.json()
            except:
                return self.responsehandler.Default.nodata()

            match data["data"]["action"]:
                case "ban":
                    return await self.moderation.banUser(data["data"], clients, BaseVars)
            

        except Exception as e:
            match isinstance(e, KeyError):
                case True:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.incorrectdata(e)
                case _:
                    await self.webhook.traceback_payload(traceback.format_exc())
                    return self.responsehandler.Default.error(traceback.format_exc())

    @user_router.put("/v3/user/favourites/sync")
    async def userFavsSync(self, request: Request):
        authCheck = await self.authenticator.auth(request=request)
        match authCheck["Validation"]:
            case valid if valid == True and authCheck["AccessType"] in [
                AccessRoles.DEVELOPER.value,
                AccessRoles.STAFF.value,
                AccessRoles.USER.value,
            ]:
                pass
            case "BANNED":
                return self.responsehandler.Ban.ban(authCheck)
            case "NO-HEADERS":
                return self.responsehandler.Default.noheaders()
            case "INVALID-KEY-FORM":
                return self.responsehandler.Default.invalidkeyform()
            case _:
                return self.responsehandler.Default.unauthed()

        try:
            data = await request.json()
        except:
            return self.responsehandler.Default.nodata()
        await self.utils.setFavs(authCheck["AuthKey"], data["data"]["favourites"])
        return JSONResponse(content={"response": "Synced Favourites"}, status_code=200)


modules = [
    {"router": base_router, "name": "Base Module", "tags": ["base"]},
    {"router": user_router, "name": "User Module", "tags": ["user"]},
    {"router": avatar_router, "name": "Avatars Module", "tags": ["avatar"]},
    {"router": testing_router, "name": "Testing Module", "tags": ["testing"]},
    {"router": websocket_router, "name": "Websocket Module", "tags": ["websocket"]},
    {"router": tags_router, "name": "Tags Module", "tags": ["tag"]},
    {"router": admin_router, "name": "Tags Module", "tags": ["tag"]}
]

for module in modules:
    try:
        app.include_router(module["router"], tags=module["tags"])
        BaseVars.log.success(f"Loaded {module['name']}")
    except:
        BaseVars.log.error(f"Couldn't Load {module['name']}: {traceback.format_exc()}")
