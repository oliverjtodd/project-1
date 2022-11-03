from fastapi.responses import JSONResponse
from Libs.Logger import Logger


log = Logger()

class Handler:
    
    def globalresponse(self, content, status):
        return JSONResponse(content=content, status_code=status)
    
    class Auth:
        @staticmethod
        def authinvalidkeyform():
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {
                        "message": "Key does not match correct format",
                    },
                },
                status_code=403,
            )
        @staticmethod
        def authbanned(authCheck: dict):
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {
                        "message": "This key is banned, please contact blaze",
                        "ban_reason": authCheck["BanReason"],
                    },
                },
                status_code=403,
            )
        @staticmethod
        def authnoheaders():
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {
                        "message": "Authorization header is required",
                    },
                },
                status_code=401,
            )
        @staticmethod
        def authwronghwid():
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {
                        "message": "HWID is invalid",
                    },
                },
                status_code=401,
            )
        @staticmethod
        def authinvaliduseragent():
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {
                        "message": "User Agent generation vaild to verify user authenticity",
                    },
                },
                status_code=401,
            )
        @staticmethod
        def authnoversion():
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {"message": "Version header required"},
                },
                status_code=401,
            )
        @staticmethod
        def authoutdated():
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {"message": "Loader is outdated"},
                },
                status_code=401,
            )
        @staticmethod
        def authunauthorised():
            return JSONResponse(
                content={
                    "api": {"Valid": False},
                    "response": {"message": "Not authorized"},
                },
                status_code=401,
            )
        @staticmethod
        def authinvalidrelease():
            return JSONResponse(
                content={
                        "api": {"Valid": False},
                        "response": "Release is not valid"
                    },
                    status_code=401
            )
    
    class Admin:
        @staticmethod
        def onlineusers(connections):
            return JSONResponse(
                content={"connected_users": connections}, status_code=200
            )
        @staticmethod
        def noonlineusers():
            return JSONResponse(
                content={"response": "No users online"}, status_code=404
            )
        @staticmethod
        def broadcast(clients):
            return JSONResponse(
                content={
                    "response": f"Message was sent to {clients} connected clients"
                },
                status_code=200,
            )
        @staticmethod
        def directbroadcast(u_name, d_name):
            return JSONResponse(
                content={
                    "response": f"Message was sent to {u_name} by developer {d_name}"
                },
                status_code=200,
            )
    class Ban:
        @staticmethod
        def ban(authCheck: dict):
            return JSONResponse(
                content={
                    "response": "This key is banned",
                    "ban_reason": authCheck["BanReason"],
                },
                status_code=403,
        )
    
    class Default:
        @staticmethod
        def invalidkeyform():
            return JSONResponse(
                content={"response": "Key does not match correct format"}, status_code=403
            )
        @staticmethod
        def unauthed():
            return JSONResponse(content={"response": "Not authorized"}, status_code=401)
        @staticmethod
        def noheaders():
            return JSONResponse(
                content={"response": "Authorization header is required"}, status_code=401
            )
        @staticmethod
        def incorrectdata(key):
            return JSONResponse(
                content={"response": f"Invalid request body, missing: {key}"}, status_code=500
            )
        @staticmethod
        def invaliddata():
            return JSONResponse(
                content = {"response": "Request body is invalid, check syntax"}
            )
        @staticmethod
        def nodata():
            return JSONResponse(
                content={"response": "No data was sent to the server"}, status_code=200
            )
        @staticmethod
        def error(e: str):
            e = e.replace("\n", "")
            return JSONResponse(
                content={"response": "An internal exception occured", "traceback": f"{e}"},
                status_code=500,
            )

    class Hwid:
        @staticmethod
        def hwidresetsuccess():
            return JSONResponse(content={"response": "HWID was reset"}, status_code=200)

    class Moderation:
        @staticmethod
        def setban(user, reasonforban):
            return JSONResponse(
                content={"response": f"User ({user}) was banned for ({reasonforban})"},
                status_code=200,
            )
        @staticmethod
        def unsetban(user):
            return JSONResponse(
                content={"response": f"User ({user}) was unbanned"}, status_code=200
            )

    class Avatar:
        @staticmethod
        def updateavatar():
            return JSONResponse(
                content={
                    "response": "Updated existing avatar in database"
                },
                status_code=200,
            )
        @staticmethod
        def conflictavatar():
            return JSONResponse(
                content={
                    "response": "Avatar already exists in database"
                },
                status_code=409,
            )
        @staticmethod
        def addavatar():
            return JSONResponse(
                content={"response": "Added avatar to database"},
                status_code=200,
            )