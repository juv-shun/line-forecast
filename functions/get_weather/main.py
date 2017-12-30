import os
import logging
from xml.etree import ElementTree

import arrow
import boto3
import requests
import yaml

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')


def handle(event, context):
    today = arrow.get(event['time']).to('Asia/Tokyo')

    # 天気予報を取得
    weather = get_weather(pref='東京', area='東京地方', dt=today)
    logger.info("Today's weather: %s" % weather)

    # ユーザー情報を取得
    users = get_users()

    # 各ユーザーへの通知メッセージをユーザー情報に追加
    users = add_message(weather, users)

    # 通知スケジュールをDBに保存
    save(users)
    logger.info("Notification: %s" % users)


def get_weather(pref, area, dt):
    # 都道府県名から都道府県IDを取得
    obj = s3.Object(os.environ.get('BUCKET_NAME'),
                    os.environ.get('PREF_OBJ_KEY'))
    pref_ids = yaml.load(obj.get()['Body'].read())
    pref_id = pref_ids[pref]

    # URL先からxml情報を取得し、解析
    res = requests.get(f"http://www.drk7.jp/weather/xml/{pref_id}.xml")
    res.encoding = 'UTF-8'

    dt = dt.strftime('%Y/%m/%d')
    path = f".//area[@id='{area}']/info[@date='{dt}']/rainfallchance/period"

    return {elem.get('hour'): int(elem.text)
            for elem in ElementTree.fromstring(res.text).findall(path)}


def get_users():
    table = dynamodb.Table(os.environ.get('TABLE_NAME'))
    attrs = ['id', 'timing', 'percent']
    return table.scan(AttributesToGet=attrs)['Items']


def add_message(weather, users):
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


def save(users):
    table = dynamodb.Table(os.environ.get('TABLE_NAME'))
    for user in users:
        key = {'id': user['id']}
        values = {'message': {'Value': user['msg'], 'Action': 'PUT'}}
        table.update_item(Key=key, AttributeUpdates=values)


if __name__ == '__main__':
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    handle({'time': '2017-12-30T22:00:00Z'}, None)
