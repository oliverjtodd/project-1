import re
import traceback
import datetime
from aioify import aioify
from Libs.Schema import WebsocketBody
from Libs.Shazam.SongFinder import ShazamUtil
from Libs.Webhooks import Webhook
from Libs.HttpResponseHandler import Handler
from Libs.Logger import Logger
from Libs.DataModel import AccessRoles, DataModel
from Core.BaseVars import baseVars


def sanitise_input(data):
    # data = str(data).replace("'", "")
    data = str(data).replace('"', "")
    data = str(data).replace("}", "")
    data = str(data).replace("{", "")
    data = str(data).replace("[", "")
    data = str(data).replace("]", "")
    data = str(data).replace("$", "")
    return data


class Utils:
    def __init__(self, BaseVars: baseVars):
        self.BaseVars = BaseVars
        self.db = BaseVars.db["BlazesMod"]
        self.users = self.db["Users"]
        self.avatars = self.db["Avatars"]
        self.avatar_search_log = self.db["AvatarSearchLog"]
        self.blacklisted_authors = self.db["BlacklistedAuthors"]
        self.search_avatar_webhookURL = BaseVars.SEARCH_AVATAR_WEBHOOK_URL
        self.apitraceback_webookURL = BaseVars.API_TRACEBACK_WEBHOOK_URL
        self.BaseVars = BaseVars
        self.webhook = Webhook(BaseVars)
        self.responsehandler = Handler()
        self.log = Logger()
        self.shazam_u: ShazamUtil = aioify(obj=ShazamUtil(self.log), name="shazam")

    # async def shazamFunc(self, data):
    #    audio_bytes = base64.b64decode(data['data'])
    #    res = await self.shazam_u.song_name(audio_bytes)
    #    payload = {
    #        "data" : None
    #    }
    #    if res['short_result'] != None:
    #        payload['data'] = {
    #            "song_name" : res['short_result']['name'],
    #            "song_artist" : res['short_result']['artist'],
    #            "song_covers" : res['short_result']['images'],
    #            "song_full_title" : res['short_result']['full_title'],
    #            "song_youtube_url" : res['short_result']['youtube_results']['result'][0]['link']
    #        }
    #        return JSONResponse(content=payload, status_code = 200)
    #    else:
    #        payload['data'] = "No song found"
    #        return JSONResponse(content=payload, status_code = 404)

    async def setFavs(self, authkey, favs):
        result = await self.users.find_one({"_id": sanitise_input(authkey)})
        if result != None:
            await self.users.update_one(
                result, {"$set": {"Favs": {"AvatarFavorites": favs}}}
            )

    # async def fetchExtension(self, data):
    #    extension = data['data']['access']
    #    if extension in self.BaseVars.extension_access_roles:
    #        with open(f"Extensions/{extension}.dll") as data:
    #            data = data.read()

    async def addAvatar(
        self, _: dict, decider: dict | WebsocketBody, websocket: bool = False
    ):
        datamodel = DataModel()
        avatar_d = _["payload"]["data"] if websocket != False else _

        async def call_avatar():
            x = await self.blacklisted_authors.find_one(
                {"_id": sanitise_input(avatar_d["AuthorID"])}
            )
            match x:
                case None:
                    IsBlacklisted = False
                case _:
                    match avatar_d["ReleaseStatus"]:
                        case "private":
                            IsBlacklisted = True
                        case "public":
                            IsBlacklisted = False
            return {
                "AvatarStruct": datamodel.avatarModel(avatar_d, IsBlacklisted),
                "Blacklisted": IsBlacklisted,
            }

        _id = {"_id": sanitise_input(avatar_d["_id"])}
        x = await self.avatars.find_one(_id)
        match x:
            case None:
                avatar_d["LoggedBy"] = (
                    decider["DiscordName"] if websocket == False else decider.Name
                )
                avatar_d["LastUpdatedBy"] = None
                avatar_d["TimeDetected"] = int(datetime.datetime.now().timestamp())
                avatar_d["TimeUpdated"] = 0
                avatar_data = await call_avatar()
                await self.avatars.insert_one(avatar_data["AvatarStruct"])
                match websocket:
                    case False:
                        await self.webhook.avataradded_payload(decider, avatar_d)
                        return self.responsehandler.Avatar.addavatar()
                    case _:
                        await self.webhook.websocket_avataradded_payload(decider, _)
                        match avatar_data["Blacklisted"]:
                            case False:
                                await self.webhook.websocket_avataradded_public_payload(
                                    _
                                )
                        await self.BaseVars.ConnectionManager.send_payload(
                            {
                                "payload": {
                                    "type": "AvatarResponse",
                                    "data": "Added avatar to database",
                                }
                            },
                            decider,
                        )
            case _:
                match int(avatar_d["Version"]):
                    case accept if accept > int(x["Version"]):
                        avatar_d["LoggedBy"] = (
                            x["LoggedBy"]
                            if x["LoggedBy"] != None
                            else decider["DiscordName"]
                            if websocket == False
                            else decider.Name
                        )
                        avatar_d["LastUpdatedBy"] = (
                            decider["DiscordName"]
                            if websocket == False
                            else decider.Name
                        )
                        avatar_d["TimeDetected"] = (
                            x["TimeDetected"]
                            if x["TimeDetected"] != 0
                            else int(datetime.datetime.now().timestamp())
                        )
                        avatar_d["TimeUpdated"] = int(
                            datetime.datetime.now().timestamp()
                        )
                        avatar_data = await call_avatar()
                        await self.avatars.update_one(
                            _id, {"$set": avatar_data["AvatarStruct"]}
                        )
                        match websocket:
                            case False:
                                await self.webhook.avataradded_payload(
                                    decider, avatar_d, True, x["Version"]
                                )
                                return self.responsehandler.Avatar.updateavatar()
                            case _:
                                await self.webhook.websocket_avataradded_payload(
                                    decider, _, True, x["Version"]
                                )
                                match avatar_data["Blacklisted"]:
                                    case False:
                                        await self.webhook.websocket_avataradded_public_payload(
                                            _, True, x["Version"]
                                        )
                                await self.BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "AvatarResponse",
                                            "data": "Updated existing avatar in database",
                                        }
                                    },
                                    decider,
                                )
                    case _:
                        match websocket:
                            case False:
                                return self.responsehandler.Avatar.conflictavatar()
                            case _:
                                await self.BaseVars.ConnectionManager.send_payload(
                                    {
                                        "payload": {
                                            "type": "AvatarResponse",
                                            "data": "Avatar already exists in database",
                                        }
                                    },
                                    decider,
                                )

    async def Search(
        self,
        decider: dict | WebsocketBody,
        search_type: str,
        query: str,
        fields: list,
        websocket: bool = False,
    ):
        datamodel = DataModel()
        try:
            if len(query) <= 2:
                res = {
                    "results": [
                        {
                            "_id": "CANT_SEARCH_LESS_THAN_TWO",
                            "AssetURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "AuthorID": "CANT_SEARCH_LESS_THAN_TWO",
                            "AuthorName": "CANT_SEARCH_LESS_THAN_TWO",
                            "AvatarName": "CANT_SEARCH_LESS_THAN_TWO",
                            "Description": "CANT_SEARCH_LESS_THAN_TWO",
                            "Featured": True,
                            "ImageURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "ReleaseStatus": "public",
                            "ThumbnailImageURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "Version": 0,
                            "BlacklistedFromSearch": False,
                            "Tags": [],
                            "Version": 0,
                            "TimeDetected": 0,
                            "TimeUpdated": 0,
                            "LoggedBy": None,
                            "LastUpdatedBy": None,
                        }
                    ]
                }
                match websocket:
                    case False:
                        return self.responsehandler.globalresponse(res, 403)
                    case _:
                        return res
            if len(query) == 0:
                res = {
                    "results": [
                        {
                            "_id": "CANT_LEAVE_INPUT_BLANK",
                            "AssetURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "AuthorID": "CANT_LEAVE_INPUT_BLANK",
                            "AuthorName": "CANT_LEAVE_INPUT_BLANK",
                            "AvatarName": "CANT_LEAVE_INPUT_BLANK",
                            "Description": "CANT_LEAVE_INPUT_BLANK",
                            "Featured": True,
                            "ImageURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "ReleaseStatus": "public",
                            "ThumbnailImageURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "Version": 0,
                            "BlacklistedFromSearch": False,
                            "Tags": [],
                            "Version": 0,
                            "TimeDetected": 0,
                            "TimeUpdated": 0,
                            "LoggedBy": None,
                            "LastUpdatedBy": None,
                        }
                    ]
                }
                match websocket:
                    case False:
                        return self.responsehandler.globalresponse(res, 403)
                    case _:
                        return res

            if search_type not in [
                "AvatarName",
                "AuthorID",
                "AuthorName",
                "Description",
                "AvatarID",
            ]:
                res = {
                    "results": [
                        {
                            "_id": "NOT_A_VALID_SEARCH_TYPE",
                            "AssetURL": "https://cdn.wtfblaze.com/assets/images/client/Blaze_2.png",
                            "AuthorID": "NOT_A_VALID_SEARCH_TYPE",
                            "AuthorName": "NOT_A_VALID_SEARCH_TYPE",
                            "AvatarName": "NOT_A_VALID_SEARCH_TYPE",
                            "Description": "NOT_A_VALID_SEARCH_TYPE",
                            "Featured": True,
                            "ImageURL": "https://cdn.wtfblaze.com/assets/images/client/Blaze_2.png",
                            "ReleaseStatus": "public",
                            "ThumbnailImageURL": "https://cdn.wtfblaze.com/assets/images/client/Blaze_2.png",
                            "BlacklistedFromSearch": False,
                            "Tags": [],
                            "Version": 0,
                            "TimeDetected": 0,
                            "TimeUpdated": 0,
                            "LoggedBy": None,
                            "LastUpdatedBy": None,
                        }
                    ]
                }
                match websocket:
                    case False:
                        return self.responsehandler.globalresponse(res, 403)
                    case _:
                        return res

            _searchfor = "_id" if search_type == "AvatarID" else search_type
            search_string = {
                f"{_searchfor}": {
                    "$regex": re.compile(sanitise_input(query), re.IGNORECASE)
                }
            }

            fields_s = {}
            for field in fields:
                fields_s[field] = 1

            list = {}
            match websocket:
                case False:
                    match decider["AccessType"]:
                        case valid if valid in [
                            AccessRoles.DEVELOPER.value,
                            AccessRoles.STAFF.value,
                        ]:
                            limit = None
                        case AccessRoles.USER.value:
                            search_string["BlacklistedFromSearch"] = False
                            limit = 5000
                        case AccessRoles.EXTERNAL_API.value:
                            limit = 1000
                            search_string["BlacklistedFromSearch"] = False
                            self.log.error("Capped search at 1000")
                case True:
                    match decider.SocketType:
                        case valid if valid in [
                            AccessRoles.DEVELOPER.value,
                            AccessRoles.STAFF.value,
                        ]:
                            limit = None
                        case AccessRoles.USER.value:
                            search_string["BlacklistedFromSearch"] = False
                            limit = 5000
                        case AccessRoles.EXTERNAL_API.value:
                            limit = 1000
                            search_string["BlacklistedFromSearch"] = False
                            self.log.error("Capped search at 1000")

            list["results"] = await self.avatars.find(search_string, fields_s).to_list(
                length=limit
            )
            # list["results"] = await self.avatars.aggregate([{"$match" : search_string}]).to_list(length = limit)
            match websocket:
                case False:
                    self.log.info(
                        f"{decider['DiscordName']} is searching by {search_type} for {query}"
                    )
                    await self.webhook.avatarsearch_payload(
                        decider, query, search_type, len(list["results"])
                    )
                    avatar_log_dict = datamodel.avatarSearchLogModel(
                        decider,
                        search_type,
                        sanitise_input(query),
                        len(list["results"]),
                    )
                case _:
                    self.log.info(
                        f"{decider.Name} is searching by {search_type} for {query}"
                    )
                    await self.webhook.websocket_avatarsearch_payload(
                        decider, query, search_type, len(list["results"])
                    )
                    avatar_log_dict = datamodel.avatarSearchLogModel(
                        decider,
                        search_type,
                        sanitise_input(query),
                        len(list["results"]),
                        websocket=True,
                    )

            await self.avatar_search_log.insert_one(avatar_log_dict)
            if len(list["results"]) <= 0:
                list = {
                    "results": [
                        {
                            "_id": "NO_AVATARS_FOUND",
                            "AssetURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "AuthorID": "NO_AVATARS_FOUND",
                            "AuthorName": "NO_AVATARS_FOUND",
                            "AvatarName": "NO_AVATARS_FOUND",
                            "Description": "NO_AVATARS_FOUND",
                            "Featured": True,
                            "ImageURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "ReleaseStatus": "public",
                            "ThumbnailImageURL": "https://wtfblaze.com/Image/Blaze_1.png",
                            "Tags": [],
                            "Version": 0,
                            "TimeDetected": 0,
                            "TimeUpdated": 0,
                            "LoggedBy": None,
                            "LastUpdatedBy": None,
                        }
                    ]
                }
            match websocket:
                case False:
                    return self.responsehandler.globalresponse(list, 200)
                case _:
                    return list
        except:
            await self.webhook.traceback_payload(traceback.format_exc())
