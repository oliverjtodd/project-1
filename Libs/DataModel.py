from bson import Int64
from enum import Enum
from Libs.Schema import WebsocketBody


class AccessRoles(Enum):
    DEVELOPER: str = "Developer"
    STAFF: str = "Staff"
    USER: str = "User"
    SPECIAL: str = "Special"
    EXTERNAL_API: str = "External_API"


class ExtensionRoles(Enum):
    APPBOTS: str = "AppBots"


def sanitise_input(data):
    # data = str(data).replace("'", "")
    data = str(data).replace('"', "")
    data = str(data).replace("}", "")
    data = str(data).replace("{", "")
    data = str(data).replace("[", "")
    data = str(data).replace("]", "")
    return data


class DataModel:
    def userModel(
        self,
        key: str,
        discord_name: str,
        discord_id: int,
        user_hash: str,
        access_type: str,
    ):
        return dict(
            {
                "_id": sanitise_input(key),
                "HWID": None,
                "DiscordName": sanitise_input(discord_name),
                "DiscordID": Int64(discord_id),
                "UserHash": sanitise_input(user_hash),
                "IsBanned": bool(False),
                "BanReason": sanitise_input(""),
                "AccessType": sanitise_input(access_type),
                "ExtensionAccess": [],
                "Favs": {"AvatarFavorites": {"FavoriteLists": []}},
            }
        )

    def avatarModel(self, data: dict, IsBlacklisted: str):
        tags = [] if data["Tags"] is None else data["Tags"]
        return dict(
            {
                "_id": sanitise_input(data["_id"]),
                "AssetURL": sanitise_input(data["AssetURL"]),
                "AuthorID": sanitise_input(data["AuthorID"]),
                "AuthorName": sanitise_input(data["AuthorName"]),
                "AvatarName": sanitise_input(data["AvatarName"]),
                "Description": sanitise_input(data["Description"]),
                "Featured": bool(data["Featured"]),
                "ImageURL": sanitise_input(data["ImageURL"]),
                "ReleaseStatus": sanitise_input(data["ReleaseStatus"]),
                "ThumbnailImageURL": sanitise_input(data["ThumbnailImageURL"]),
                "SupportedPlatforms": sanitise_input(data["SupportedPlatforms"]),
                "Tags": tags,
                "Version": int(data["Version"]),
                "BlacklistedFromSearch": bool(IsBlacklisted),
                "TimeDetected": int(data["TimeDetected"]),
                "TimeUpdated": data["TimeUpdated"],
                "LoggedBy": data["LoggedBy"],
                "LastUpdatedBy": data["LastUpdatedBy"],
            }
        )

    def avatarSearchLogModel(
        self,
        user: WebsocketBody | dict,
        s_type: str,
        query: str,
        count: int,
        websocket: bool = False,
    ):
        return dict(
            {
                "Username": sanitise_input(user["DiscordName"])
                if websocket is False
                else str(user.Name),
                "DiscordID": Int64(user["DiscordID"])
                if websocket is False
                else Int64(user.DID),
                "SearchType": sanitise_input(s_type),
                "Query": sanitise_input(query),
                "ResultCount": count,
            }
        )
