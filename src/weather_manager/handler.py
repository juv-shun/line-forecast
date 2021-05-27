import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import arrow

import boto3

import requests

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO")))

dynamo_config = {"endpoint_url": "http://localhost:8000"} if os.getenv("IS_LOCAL", False) else {}
dynamodb = boto3.resource('dynamodb', **dynamo_config)

WEATHER_API_URL = "http://www.drk7.jp/weather/xml/13.xml"
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']


def get_weather(dt: date) -> Dict[str, Optional[int]]:
    def get_int(n: str) -> Optional[int]:
        try:
            return int(n)
        except ValueError:
            return None

    res = requests.get(WEATHER_API_URL)
    res.encoding = 'UTF-8'

    date_ = dt.strftime('%Y/%m/%d')
    path = f".//area[@id='東京地方']/info[@date='{date_}']/rainfallchance/period"

    return {
        elem.get('hour'): get_int(elem.text)
        for elem in ElementTree.fromstring(res.text).findall(path)
    }


def get_users() -> List[Dict[str, Any]]:
    table = dynamodb.Table(DYNAMODB_TABLE)
    attrs = ['id', 'percent']
    return table.scan(AttributesToGet=attrs)['Items']


def add_message(weather: Dict[str, Optional[int]], users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    r1 = weather['06-12']
    r2 = weather['12-18']
    r3 = weather['18-24']

    for i, user in enumerate(users):
        p = user['percent']
        if p <= r1 and p <= r2 and p <= r3:
            users[i]['msg'] = 'allday'
        elif p <= r1 and p <= r2 and p > r3:
            users[i]['msg'] = 'morning_afternoon'
        elif p <= r1 and p > r2 and p <= r3:
            users[i]['msg'] = 'morning_night'
        elif p > r1 and p <= r2 and p <= r3:
            users[i]['msg'] = 'afternoon_night'
        elif p <= r1 and p > r2 and p > r3:
            users[i]['msg'] = 'morning'
        elif p > r1 and p <= r2 and p > r3:
            users[i]['msg'] = 'afternoon'
        elif p > r1 and p > r2 and p <= r3:
            users[i]['msg'] = 'night'
        elif p > r1 and p > r2 and p > r3:
            users[i]['msg'] = 'none'

    return users


def save(users: List[Dict[str, Any]]) -> None:
    table = dynamodb.Table(DYNAMODB_TABLE)
    now = arrow.now().to('Asia/Tokyo').replace(microsecond=0).isoformat()
    for user in users:
        key = {'id': user['id']}
        values = {'message': {'Value': user['msg'], 'Action': 'PUT'},
                  'last_updated': {'Value': now, 'Action': 'PUT'}}
        table.update_item(Key=key, AttributeUpdates=values)


def handle(event, context):
    now = arrow.get(event['time']) if isinstance(event, dict) and 'time' in event else arrow.now()
    weather = get_weather(dt=now.to('Asia/Tokyo').date())
    logger.info("Today's weather: %s" % weather)

    users = add_message(weather, get_users())
    save(users)
    logger.info("Notification: %s" % users)


if __name__ == '__main__':
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    handle(None, None)
