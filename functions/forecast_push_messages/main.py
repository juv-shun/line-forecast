import os
import boto3
import yaml
from datetime import datetime
from pytz import timezone
from linebot import LineBotApi
from linebot.models import TextSendMessage

BUCKET_NAME = os.environ.get('BUCKET_NAME')
HOLIDAY_OBJ_KEY = os.environ.get('HOLIDAY_OBJ_KEY')
MESSAGE_OBJ_KEY = os.environ.get('MESSAGE_OBJ_KEY')
USER_TABLE = os.environ.get('USER_TABLE')
LINE_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')
line_bot = LineBotApi(LINE_TOKEN)


def handle(event, context):
    # 現在の東京時間を取得
    time = datetime.now(timezone('Asia/Tokyo'))
    time = datetime(2017, 10, 14, 6, 15)

    # 祝日なら通知しない
    if is_holiday(time.date()):
        return 'OK'

    # 取得時刻の誤差を修正
    time = round_time(time.minute)

    # ユーザー情報を取得
    users = get_users_by_timing(time)

    # 各ユーザにメッセージを送信
    send_messages(users, get_messages())


def is_holiday(dt):
    obj = s3.Object(BUCKET_NAME, HOLIDAY_OBJ_KEY)
    holidays = yaml.load(obj.get()['Body'].read())
    if dt in holidays.keys():
        return True
    else:
        return False


def round_time(min):
    minutes = [0, 15, 30, 45]
    if min in [minute+1 for minute in minutes]:
        return min - 1
    else:
        return min


def get_users_by_timing(time):
    table = dynamodb.Table(USER_TABLE)
    attrs = ['id', 'active', 'message', 'name']
    filter = {
        'active': {
            'AttributeValueList': [True],
            'ComparisonOperator': 'EQ'
        },
        'timing': {
            'AttributeValueList': [time.strftime('%H:%M')],
            'ComparisonOperator': 'EQ'
        }
    }
    return table.scan(AttributesToGet=attrs, ScanFilter=filter)['Items']


def get_messages():
    obj = s3.Object(BUCKET_NAME, MESSAGE_OBJ_KEY)
    messages = yaml.load(obj.get()['Body'].read())
    return messages['weather_notice']


def send_messages(users, messages):
    for user in users:
        if user['active']:
            message = TextSendMessage(text=messages[user['message']])
            line_bot.push_message(user['id'], message)


if __name__ == '__main__':
    handle(None, None)
