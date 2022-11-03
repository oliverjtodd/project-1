import traceback
import uuid
import re
import hashlib
import bson
from fastapi import Request
from Libs.ConnectionManager import ConnectionManager
from Libs.Logger import Logger
from Libs.Schema import WebsocketBody
from Libs.Utils import sanitise_input
from Libs.Webhooks import Webhook
from Libs.DataModel import AccessRoles
from Core.BaseVars import baseVars


class Auth:
    def __init__(self, BaseVars: baseVars):
        self.log = Logger()
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.apitraceback_webookURL = BaseVars.API_TRACEBACK_WEBHOOK_URL
        self.websocket_webhookURL = BaseVars.WEBSOCKET_WEBHOOK_URL
        self.loaderVersion = BaseVars.LOADER_VERSION
        self.clientVersion = BaseVars.CLIENT_VERSION
        self.webhook = Webhook(BaseVars)
        self.users = self.db["Users"]

    def response(
        self,
        Validation: any,
        DiscordName: str,
        DiscordID: any,
        AuthKey: any,
        HWID: str,
        AccessType: str,
        BanReason: any,
        IsBanned: bool,
        Extensions: list,
        UserHash: str,
        Headers: any,
    ):
        return {
            "Validation": Validation,
            "DiscordName": DiscordName,
            "DiscordID": DiscordID,
            "AuthKey": AuthKey,
            "HWID": HWID,
            "AccessType": AccessType,
            "BanReason": BanReason,
            "IsBanned": IsBanned,
            "Extensions": Extensions,
            "UserHash": UserHash,
            "Headers": dict(Headers),
        }

    async def auth(
        self,
        request: Request,
        loader: bool = False,
        param: str | bool = False,
        data: dict | bool = False,
    ):
        try:
            try:
                match param:
                    case auth if isinstance(auth, str):
                        key = auth.strip()
                    case False:
                        key = request.headers["Authorization"]
                user_agent = request.headers["User-Agent"]
            except:
                return self.response(
                    Validation="NO-HEADERS",
                    DiscordName="NO-HEADERS",
                    DiscordID=0,
                    AuthKey="NO-HEADERS",
                    HWID="NO-HEADERS",
                    AccessType="NO-HEADERS",
                    BanReason=None,
                    IsBanned=False,
                    Extensions=[],
                    UserHash="NO-HEADERS",
                    Headers=request.headers,
                )
            match re.match(
                r"BM_[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}_[a-f0-9]{32}",
                key,
            ):
                case None:
                    return self.response(
                        Validation="INVALID-KEY-FORM",
                        DiscordName="INVALID-KEY-FORM",
                        DiscordID=0,
                        AuthKey="INVALID-KEY-FORM",
                        HWID="INVALID-KEY-FORM",
                        AccessType="INVALID-KEY-FORM",
                        BanReason=None,
                        IsBanned=False,
                        Extensions=[],
                        UserHash="INVALID-KEY-FORM",
                        Headers=request.headers,
                    )
                case _:
                    pass

            if loader is True:
                try:
                    version_check = request.headers["LoaderVersion"]
                    if version_check != self.loaderVersion:
                        return self.response(
                            Validation="OUTDATED",
                            DiscordName="OUTDATED",
                            DiscordID=0,
                            AuthKey="OUTDATED",
                            HWID="OUTDATED",
                            AccessType="OUTDATED",
                            BanReason=None,
                            IsBanned=False,
                            Extensions=[],
                            UserHash="OUTDATED",
                            Headers=request.headers,
                        )
                except:
                    return self.response(
                        Validation="NO-VERSION",
                        DiscordName="NO-VERSION",
                        DiscordID=0,
                        AuthKey="NO-VERSION",
                        HWID="NO-VERSION",
                        AccessType="NO-VERSION",
                        BanReason=None,
                        IsBanned=False,
                        Extensions=[],
                        UserHash="NO-VERSION",
                        Headers=request.headers,
                    )

            x = await self.users.find_one({"_id": sanitise_input(key)})
            match x:
                case None:
                    return self.response(
                        Validation=False,
                        DiscordName="UN-AUTHORIZED",
                        DiscordID=0,
                        AuthKey="UN-AUTHORIZED",
                        HWID="UN-AUTHORIZED",
                        AccessType="UN-AUTHORIZED",
                        BanReason=None,
                        IsBanned=False,
                        Extensions=[],
                        UserHash="UN-AUTHORIZED",
                        Headers=request.headers,
                    )
                case _:
                    if loader is True:
                        match x["HWID"]:
                            case None:
                                await self.users.update_one(
                                    {"_id": x["_id"]},
                                    {
                                        "$set": {
                                            "HWID": data["HWID"]
                                        }
                                    },
                                )

                            case valid if valid != data["HWID"]:
                                return self.response(
                                    Validation="INVALID-HWID",
                                    DiscordName=x["DiscordName"],
                                    DiscordID=x["DiscordID"],
                                    AuthKey=x["_id"],
                                    HWID=x["HWID"],
                                    AccessType=x["AccessType"],
                                    BanReason=x["BanReason"],
                                    IsBanned=x["IsBanned"],
                                    Extensions=x["ExtensionAccess"],
                                    UserHash=x["UserHash"],
                                    Headers=request.headers,
                                )

                        user_hash = str(
                            hashlib.md5(
                                str(f"{x['_id']}_{x['HWID']}").encode()
                            ).hexdigest()
                        )
                        incoming_user_hash = re.findall(r"[a-f0-9]{32}", user_agent)
                        incoming_user_hash = (
                            str(incoming_user_hash[0])
                            if len(incoming_user_hash) > 0
                            else None
                        )
                        real_user_agent = (
                            f"BlazeClient ({self.loaderVersion}, {user_hash})"
                        )
                        incoming_user_agent = f"BlazeClient ({self.loaderVersion}, {incoming_user_hash})"
                        if incoming_user_agent != real_user_agent:
                            return self.response(
                                Validation="INVALID-USER-AGENT",
                                DiscordName=x["DiscordName"],
                                DiscordID=x["DiscordID"],
                                AuthKey=x["_id"],
                                HWID=x["HWID"],
                                AccessType=x["AccessType"],
                                BanReason=x["BanReason"],
                                IsBanned=x["IsBanned"],
                                Extensions=x["ExtensionAccess"],
                                UserHash=x["UserHash"],
                                Headers=request.headers,
                            )
                    match bool(x["IsBanned"]):
                        case False:
                            return self.response(
                                Validation=True,
                                DiscordName=x["DiscordName"],
                                DiscordID=x["DiscordID"],
                                AuthKey=x["_id"],
                                HWID=x["HWID"],
                                AccessType=x["AccessType"],
                                BanReason=x["BanReason"],
                                IsBanned=x["IsBanned"],
                                Extensions=x["ExtensionAccess"],
                                UserHash=x["UserHash"],
                                Headers=request.headers,
                            )
                        case True:
                            return self.response(
                                Validation="BANNED",
                                DiscordName=x["DiscordName"],
                                DiscordID=x["DiscordID"],
                                AuthKey=x["_id"],
                                HWID=x["HWID"],
                                AccessType=x["AccessType"],
                                BanReason=x["BanReason"],
                                IsBanned=x["IsBanned"],
                                Extensions=x["ExtensionAccess"],
                                UserHash=x["UserHash"],
                                Headers=request.headers,
                            )
        except:
            await self.webhook.traceback_payload(traceback.format_exc())

    async def websocket_auth(
        self,
        user: dict,
        websocket: WebsocketBody,
        discord_id: bson.Int64,
        ConnectionManager: ConnectionManager,
        userhash: str,
        clients: WebsocketBody,
    ):
        try:
            websocket.SocketType = str(user["AccessType"])
            websocket.Name = str(user["DiscordName"])
            websocket.DID = int(user["DiscordID"])
            websocket.Authkey = str(user["_id"])
            websocket.HWID = str(user["HWID"])
            websocket.UserHash = str(user["UserHash"])
            websocket.Extensions = list(user["ExtensionAccess"])

            generate_hash = str(hashlib.md5(websocket.Name.encode()).hexdigest())
            generate_uuid = str(uuid.uuid4())
            websocket.ID = f"SOCKET_{generate_uuid}_{generate_hash}"

            if userhash != user["UserHash"]:
                await self.webhook.websocket_disconnect_hash_payload(websocket)
                self.log.warning(
                    f"{user['DiscordName']} is trying to connect to the websocket but supplied hash is incorrect, refusing connection"
                )
                return {"Result": "IncorrectHash", "AccessLevel": websocket.SocketType}
            if user["IsBanned"] is True:
                await self.webhook.websocket_disconnect_banned_payload(websocket)
                self.log.warning(
                    f"{user['DiscordName']} is trying to connect to the websocket but is banned, refusing connection"
                )
                return {"Result": "IsBanned", "AccessLevel": websocket.SocketType}

            if websocket.SocketType not in [role.value for role in AccessRoles]:
                await self.webhook.websocket_disconnect_unauthorised_payload(websocket)
                self.log.warning(
                    f"{user['DiscordName']} is attempting to connect to the websocket but does not have the access permissions"
                )
                return {"Result": "IsUnAuthorised", "AccessLevel": websocket.SocketType}

            if websocket.Authkey in ConnectionManager.ws_connected_keys:
                await self.webhook.websocket_disconnect_duplicate_payload(websocket)
                self.log.warning(
                    f"{user['DiscordName']} is trying to connect to the websocket but is a duplicate, refusing connection"
                )
                return {"Result": "IsDuplicate", "AccessLevel": websocket.SocketType}

            try:
                if ConnectionManager.ws_connections[discord_id]:
                    ConnectionManager.remove_connection(discord_id)
            except KeyError:
                pass

            await ConnectionManager.accept_socket(websocket)
            ConnectionManager.add_key(websocket)
            ConnectionManager.append_socket(websocket)
            ConnectionManager.add_connection(discord_id, websocket)
            await self.webhook.websocket_connect_payload(websocket)
            self.log.info(f"{websocket.Name} has connected to the websocket")
            for client in clients:
                if client.SocketType in [
                    AccessRoles.DEVELOPER.value,
                    AccessRoles.STAFF.value,
                ]:
                    await ConnectionManager.send_payload(
                        {
                            "payload": {
                                "type": "OnUserOnline",
                                "data": {
                                    "name": websocket.Name,
                                    "level": websocket.SocketType,
                                },
                            }
                        },
                        client,
                    )
            return {"Result": "Accepted", "AccessLevel": websocket.SocketType}
        except:
            await self.webhook.traceback_payload(traceback.format_exc())
