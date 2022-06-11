import base64
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict

from .weatherbot import WeatherBot

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO")))

weather_bot = WeatherBot(os.environ["LINE_ACCESS_TOKEN"])

LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]


def verify_signature(request: Dict[str, Any]) -> bool:
    if "x-line-signature" not in request["headers"]:
        return False
    line_sign = request["headers"]["x-line-signature"]
    body = request["body"]

    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256
    ).digest()

    return base64.b64encode(hash) == line_sign.encode("utf-8")


def handle(event, context):
    logger.info(json.dumps(event, ensure_ascii=False, indent=3))

    if not verify_signature(event):
        logger.warning("Invalid signature.")
        return {
            "statusCode": 400,
            "body": "",
        }

    body = json.loads(event["body"])
    logger.info(json.dumps(body, ensure_ascii=False, indent=3))

    for event in body["events"]:
        weather_bot.reply(event)

    return "ok"
