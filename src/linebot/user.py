import os
import logging
from typing import Optional

import arrow

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo_config = (
    {"endpoint_url": "http://localhost:8000"} if os.getenv("IS_LOCAL", False) else {}
)
dynamodb = boto3.resource("dynamodb", **dynamo_config)

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


class User:
    @classmethod
    def find(cls, user_id) -> Optional["User"]:
        table = dynamodb.Table(DYNAMODB_TABLE)
        res = table.get_item(Key={"id": user_id})
        return (
            User(
                id=res["Item"]["id"],
                name=res["Item"]["name"],
                timing=res["Item"]["timing"],
                percent=res["Item"]["percent"],
                area=res["Item"]["area"],
                active=res["Item"]["active"],
                talk_status=res["Item"]["talk_status"],
                message=res["Item"]["message"],
            )
            if "Item" in res
            else None
        )

    def __init__(
        self,
        id,
        name,
        timing="06:15",
        percent=40,
        area="東京",
        active=True,
        talk_status="Wait",
        message="none",
    ):
        self.id = id
        self.name = name
        self.timing = timing
        self.percent = percent
        self.area = area
        self.active = active
        self.talk_status = talk_status
        self.message = message

    def save(self):
        dynamodb.Table(DYNAMODB_TABLE).put_item(
            Item={
                "id": self.id,
                "name": self.name,
                "timing": self.timing,
                "percent": self.percent,
                "area": self.area,
                "active": self.active,
                "talk_status": self.talk_status,
                "message": self.message,
                "last_updated": arrow.now().replace(microsecond=0).isoformat(),
            }
        )
