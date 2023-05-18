import json
import logging
import os

import chardet
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def line_notify(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "message": msg,
    }
    response = requests.post(
        "https://notify-api.line.me/api/notify",
        headers=headers,
        data=data,
    )
    logger.info("Line notify response status: %s", response.status_code)
    return response.status_code


def process_payload(payload_str, cryptocurrency_name):
    message_list = payload_str.split("｜")
    if len(message_list) == 4:  # 空 or 多 or 加倉 or 減倉
        return (
            (
                {
                    "策略名稱": message_list[0],
                    "操作": message_list[1],
                    "時間": message_list[2],
                    "價位": message_list[3],
                },
            ),
            f"{cryptocurrency_name}\n策略名稱:{message_list[0]}\n操作:{'📈' if '多方' in message_list[1] else '📉'}{message_list[1]}\n時間:{message_list[2]}\n價位:{message_list[3]}",
        )
    elif len(message_list) == 3:  # 九轉
        return (
            {
                "策略名稱": message_list[0],
                "時間": message_list[1],
                "九轉": message_list[2],
            },
            f"{cryptocurrency_name}\n策略名稱:{message_list[0]}\n時間:{message_list[1]}\n九轉:{message_list[2]}",
        )
    else:
        raise ValueError("Invalid payload format")


app = FastAPI()


@app.post("/tom-tradingview-webhook/{param}")
async def tradingview_webhook(request: Request, param: str):
    try:
        payload_bytes = await request.body()
        detected_encoding = chardet.detect(payload_bytes)["encoding"]
        payload_str = payload_bytes.decode(detected_encoding).replace('"', "")

        if "｜" in payload_str:
            payload, msg = process_payload(payload_str)
        else:
            raise ValueError("Invalid payload format")

        line_notify(LINE_NOTIFY_TOKEN, msg)
        logger.info("Payload received and processed")
        return {"message": "Payload received and processed"}

    except (UnicodeDecodeError, ValueError) as e:
        logger.error("Failed to process payload: %s", str(e))
        return {"error": f"Failed to process payload: {str(e)}"}
