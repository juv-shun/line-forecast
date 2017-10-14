import os
import boto3
import requests
import yaml
from datetime import datetime
from pytz import timezone
from xml.etree import ElementTree

BUCKET_NAME = os.environ.get('BUCKET_NAME')
PREF_OBJ_KEY = os.environ.get('PREF_OBJ_KEY')
USER_TABLE = os.environ.get('USER_TABLE')

PERCENTS = [30, 40, 50]
TIMINGS = ['06:15', '06:30', '06:45', '07:00', '07:15',
           '07:30', '07:45', '08:00', '08:15', '08:30', '08:45']

dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')


def handle(event, context):
    # 現在の東京日時を取得
    today = datetime.now(timezone('Asia/Tokyo')).date()

    # 天気予報を取得
    weather = get_weather(pref='東京', area='東京地方', dt=today)

    # ユーザー情報を取得
    users = get_users()

    # 各ユーザーへの通知メッセージをユーザー情報に追加
    users = add_message(weather, users)

    # 通知スケジュールをDBに保存
    save(users)


def get_weather(pref, area, dt):
    # 都道府県名から都道府県IDを取得
    obj = s3.Object(BUCKET_NAME, PREF_OBJ_KEY)
    pref_ids = yaml.load(obj.get()['Body'].read())
    pref_id = pref_ids[pref]

    # URL先からxml情報を取得し、解析
    url = "http://www.drk7.jp/weather/xml/%s.xml" % pref_id
    res = requests.get(url)
    res.encoding = 'UTF-8'

    path = ".//area[@id='%s']/info[@date='%s']/rainfallchance/period"\
           % (area, dt.strftime('%Y/%m/%d'))

    return {elem.get('hour'): int(elem.text)
            for elem in ElementTree.fromstring(res.text).findall(path)}


def get_users():
    table = dynamodb.Table(USER_TABLE)
    attrs = ['id', 'name', 'timing', 'percent']
    filter = {
        'active': {
            'AttributeValueList': [True],
            'ComparisonOperator': 'EQ'
        }
    }
    return table.scan(AttributesToGet=attrs, ScanFilter=filter)['Items']


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
    table = dynamodb.Table(USER_TABLE)
    for user in users:
        key = {'id': user['id']}
        values = {'message': {'Value': user['msg'], 'Action': 'PUT'}}
        table.update_item(Key=key, AttributeUpdates=values)


if __name__ == '__main__':
    handle(None, None)
