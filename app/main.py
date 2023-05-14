import json
import os

import chardet
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")


def line_notify(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "message": json.dumps(msg, ensure_ascii=False),
    }
    response = requests.post(
        "https://notify-api.line.me/api/notify",
        headers=headers,
        data=data,
    )
    print(response.status_code)
    return response.status_code


def process_payload(payload_str):
    message_list = payload_str.split("｜")
    if len(message_list) == 4:  # 空 or 多 or 加倉 or 減倉
        return {
            "策略名稱": message_list[0],
            "操作": message_list[1],
            "時間": message_list[2],
            "價位": message_list[3],
        }
    elif len(message_list) == 3:  # 九轉
        return {
            "策略名稱": message_list[0],
            "時間": message_list[1],
            "九轉": message_list[2],
        }
    else:
        raise ValueError("Invalid payload format")


app = FastAPI()


@app.post("/tom-tradingview-webhook")
async def tradingview_webhook(request: Request):
    try:
        payload_bytes = await request.body()
        detected_encoding = chardet.detect(payload_bytes)["encoding"]
        payload_str = payload_bytes.decode(detected_encoding).replace('"', "")

        if "｜" in payload_str:
            payload = process_payload(payload_str)
        else:
            raise ValueError("Invalid payload format")

        line_notify(LINE_NOTIFY_TOKEN, payload)
        return {"message": "Payload received and processed"}

    except (UnicodeDecodeError, ValueError) as e:
        return {"error": f"Failed to process payload: {str(e)}"}
