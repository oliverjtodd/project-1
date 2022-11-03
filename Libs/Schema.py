import uuid
import hashlib
from typing import Optional
from pydantic import BaseModel
from bson import Int64


class APISchema:
    class BlacklistModel:
        class UserI(BaseModel):
            class Input(BaseModel):
                author_id: str

            data: Optional[Input] = None

        class UserO(BaseModel):
            class Output(BaseModel):
                _id: str

            data: Optional[Output] = None

    class RegisterModel:
        class RegisterOutput(BaseModel):
            class RegisterOutputBody(BaseModel):
                AuthKey: str = "Trollface"
                DiscordName: str = "VRCBot"
                DiscordID: Int64 = 894378954352381964
                IsBanned: bool = False
                BanReason: str = ""
                AccessType: str = "User"

            response: str = "Foo Bar"
            data: Optional[RegisterOutputBody] = None

        class RegisterInput(BaseModel):
            class RegisterInputBody(BaseModel):
                discordName: str
                discordID: Int64
                accessType: str

            data: Optional[RegisterInputBody] = None

    class MainResponses:
        class MainResponse(BaseModel):
            response: str = "Foo Bar"
            data: str = None

        class MainResponseNoData(BaseModel):
            response: str = "Foo Bar"

    class MiscResponses:
        class WebsocketConnectedOutputBody(BaseModel):
            connected_users: dict

        class AvatarStatsOutputBody(BaseModel):
            Authors: int = 151011
            Avatars: int = 1275899
            BlacklistedAvatars: int = 879
            SearchesMade: int = 5743
            PrivateAvatars: int = 655811
            PublicAvatars: int = 620030

    class UserModel:
        class UserOutput(BaseModel):
            AuthKey: str = "Trollface"
            HWID: str = str(uuid.uuid4())
            DiscordName: str = "VRCBot"
            DiscordID: Int64 = 894378954352381964
            UserHash: str = hashlib.md5(
                str("894378954352381964").encode("utf-8")
            ).hexdigest()
            IsBanned: bool = False
            BanReason: str = ""
            AccessType: str = "User"
            Favs: dict = {"AvatarFavorites": {"FavoriteLists"}}
            Extensions: list = []

    class AvatarModel:
        class AvatarOutput(BaseModel):
            class AvatarBody(BaseModel):
                _id: str = "avtr_b5c8ef23-46dc-48f4-844e-f5dd3b300b92"
                AssetURL: str = "https://api.vrchat.cloud/api/1/file/file_17412203-3ada-4331-a43c-d2e6a15f4e91/1/file"
                QAssetURL: str = "https://api.vrchat.cloud/api/1/file/file_17412203-3ada-4331-a43c-d2e6a15f4e91/1/file"
                AuthorID: str = "8JoV9XEdpo"
                AuthorName: str = "vrchat"
                AvatarName: str = "Nikei (Morph3D)"
                Description: str = "Nikei (Morph3D)"
                Featured: bool = True
                ImageURL: str = "https://s3-us-west-2.amazonaws.com/vrc-uploads/images/image_1200x900_2016-11-29_22-04-32.png"
                ReleaseStatus: str = "public"
                ThumbnailImageURL: str = "https://s3-us-west-2.amazonaws.com/vrc-uploads/thumbnails/866713936.thumbnail-200.png"
                Version: int = 0
                Tags: list = ["admin_featured_legacy"]
                TimeDetected: int = 0

            results: list[AvatarBody] = None

        class AvatarSearchInput(BaseModel):
            class CreateSearchBody(BaseModel):
                search_type: str = "AvatarName"
                search_query: str

            search: Optional[CreateSearchBody]


class WebsocketBody(object):
    SocketType: str
    Name: str
    DID: Int64
    Authkey: str
    HWID: str
    UserHash: str
    Extensions: list
    LobbyPlayers: list
    ID: str
