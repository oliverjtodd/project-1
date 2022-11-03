import aiohttp
import base64
import io
from fastapi.responses import JSONResponse


class CaptchaSolver:
    def __init__(self):
        self.key = "6d2ee3c276672e07f6c103619968adf0"
        self.baseURL = "http://2captcha.com"

    async def send_data(self, encoded_data):
        async with aiohttp.ClientSession() as session:
            decoded = base64.b64decode(encoded_data)
            file = io.BytesIO(decoded)
            form = aiohttp.FormData()
            form.add_field(name="key", value=self.key)
            form.add_field(name="json", value="1")
            form.add_field(
                name="file",
                value=file,
                content_type="image/png",
                filename="captcha.png",
            )
            async with session.post(f"{self.baseURL}/in.php", data=form) as result:
                result = await result.json()
                match result["status"]:
                    case 1:
                        return JSONResponse(
                            content={"response": {"id": result["request"]}},
                            status_code=201,
                        )
                    case 0:
                        return JSONResponse(
                            content={"response": "2Captcha refused data"},
                            status_code=403,
                        )

    async def receive_data(self, c_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.baseURL}/res.php?key={self.key}&action=get&id={c_id}&json=1"
            ) as result:
                result = await result.json()
                match result["status"]:
                    case 1:
                        return JSONResponse(
                            content={"response": {"captcha": result["request"]}},
                            status_code=200,
                        )
                    case 0:
                        match result["request"]:
                            case "CAPCHA_NOT_READY":
                                return JSONResponse(
                                    content={"response": "Captcha not ready"},
                                    status_code=403,
                                )
                            case "ERROR_CAPTCHA_UNSOLVABLE":
                                return JSONResponse(
                                    content={
                                        "response": "2Captcha could not solve the captcha"
                                    },
                                    status_code=403,
                                )
                            case "ERROR_WRONG_CAPTCHA_ID":
                                return JSONResponse(
                                    content={
                                        "response": "2Captcha did not recognise the ID"
                                    },
                                    status_code=403,
                                )
                            case "ERROR_DUPLICATE_REPORT":
                                return JSONResponse(
                                    content={
                                        "response": "2Captcha said too stop sending the same captcha"
                                    },
                                    status_code=403,
                                )
