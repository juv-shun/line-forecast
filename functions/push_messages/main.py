import os
import boto3
import yaml
from datetime import datetime, timedelta
from pytz import timezone
from linebot import LineBotApi
from linebot.models import TextSendMessage
from logging import (getLogger, INFO)

BUCKET_NAME = os.environ.get('BUCKET_NAME')
HOLIDAY_OBJ_KEY = os.environ.get('HOLIDAY_OBJ_KEY')
MESSAGE_OBJ_KEY = os.environ.get('MESSAGE_OBJ_KEY')
TABLE_NAME = os.environ.get('TABLE_NAME')
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)
s3 = boto3.resource('s3')
line_bot = LineBotApi(CHANNEL_ACCESS_TOKEN)
logger = getLogger()
logger.setLevel(INFO)


def handle(event, context):
    # 現在の東京時間を取得
    time = datetime.now(timezone('Asia/Tokyo'))

    # 祝日なら通知しない
    if is_holiday(time.date()):
        logger.info('it is national holiday.')
        return 'OK'

    # 取得時刻の誤差を修正
    time = round_time(time)

    # ユーザー情報を取得
    users = get_users_by_timing(time)
    if len(users) == 0:
        logger.info('there is no users to push message.')

    # 各ユーザにメッセージを送信
    send_messages(users, get_messages())


def is_holiday(dt):
    obj = s3.Object(BUCKET_NAME, HOLIDAY_OBJ_KEY)
    holidays = yaml.load(obj.get()['Body'].read())
    return dt in holidays.keys()


def round_time(time):
    base_minutes = [0, 15, 30, 45]
    for base_minute in base_minutes:
        min_diff = time.minute - base_minute
        if -1 <= min_diff and min_diff <= 3:
            return time - timedelta(minutes=min_diff)

    logger.error('Unknown timing')
    raise Exception


def get_users_by_timing(time):
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
        if user['active'] is True and user['message'] is not None:
            message = TextSendMessage(text=messages[user['message']])
            line_bot.push_message(user['id'], message)
            logger.info("Notification: %s -> %s"
                        % (user['name'], user['message']))


if __name__ == '__main__':
    from logging import StreamHandler, Formatter

    handler = StreamHandler()
    handler.setFormatter(Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    handle(None, None)
