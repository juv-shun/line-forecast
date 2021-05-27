import json
import logging
import os
import datetime
from typing import Any, Dict, List

import arrow

import boto3

from linebot import LineBotApi
from linebot.models import TextSendMessage

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO")))

dynamo_config = {"endpoint_url": "http://localhost:8000"} if os.getenv("IS_LOCAL", False) else {}
dynamodb = boto3.resource('dynamodb', **dynamo_config)
s3 = boto3.resource('s3')
linebot = LineBotApi(os.environ['LINE_ACCESS_TOKEN'])

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
S3_BUCKET = os.environ['S3_BUCKET']
S3_MESSAGE_OBJ_KEY = os.environ['S3_MESSAGE_OBJ_KEY']


def is_holiday(dt: arrow.arrow.Arrow) -> bool:
    return False


def get_users_by_timing(time_: datetime.time) -> List[Dict[str, Any]]:
    table = dynamodb.Table(DYNAMODB_TABLE)
    attrs = ['id', 'active', 'message', 'name', 'last_updated']
    filter = {
        'active': {
            'AttributeValueList': [True],
            'ComparisonOperator': 'EQ'
        },
        'timing': {
            'AttributeValueList': [time_.strftime('%H:%M')],
            'ComparisonOperator': 'EQ'
        }
    }
    return table.scan(AttributesToGet=attrs, ScanFilter=filter)['Items']


def get_push_messages() -> Dict[str, str]:
    obj = s3.Object(S3_BUCKET, S3_MESSAGE_OBJ_KEY)
    messages = json.load(obj.get()['Body'])
    return messages['weather_notice']


def handle(event, context):
    now = arrow.get(event['time']) if isinstance(event, dict) and 'time' in event else arrow.now()
    now = now.to('Asia/Tokyo')

    if is_holiday(now):
        logger.info('it is national holiday.')
        return

    # 時刻を丸め込み
    now = now.replace(minute=now.minute - now.minute % 5,
                      second=0, microsecond=0)

    messages = get_push_messages()
    for user in get_users_by_timing(now.time()):
        if arrow.get(user['last_updated']) - arrow.now().to('Asia/Tokyo') > datetime.timedelta(hours=20):
            logger.warn('weather is not updated over 20 hours')
            continue
        if user['message'] == 'none':
            continue
        linebot.push_message(user['id'], TextSendMessage(text=messages[user['message']]))
        logger.info(f"to: {user['name']}, message: {messages[user['message']]}")


if __name__ == '__main__':
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    handle({'time': arrow.now().isoformat()}, None)
