import os
import logging
import json

import arrow
import boto3
import yaml

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.resource('sns')


def handle(event, context):
    time = arrow.get(event['time']).to('Asia/Tokyo')

    # 祝日なら通知しない
    if is_holiday(time.date()):
        logger.info('it is national holiday.')
        return 'OK'

    # 取得時刻の誤差を修正
    time = time.replace(minutes=time.minute % 5 * -1)

    # ユーザー情報を取得
    users = get_users_by_timing(time)
    if len(users) == 0:
        logger.info('there is no users to push message.')

    # 各ユーザにメッセージを送信
    send_messages(users, get_messages())


def is_holiday(dt):
    obj = s3.Object(os.environ.get('BUCKET_NAME'),
                    os.environ.get('HOLIDAY_OBJ_KEY'))
    holidays = yaml.load(obj.get()['Body'].read())
    return dt in holidays.keys()


def get_users_by_timing(time):
    table = dynamodb.Table(os.environ.get('TABLE_NAME'))
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
    obj = s3.Object(os.environ.get('BUCKET_NAME'),
                    os.environ.get('MESSAGE_OBJ_KEY'))
    messages = yaml.load(obj.get()['Body'].read())
    return messages['weather_notice']


def send_messages(users, messages):
    topic = sns.Topic(os.environ.get('TOPIC_ARN'))

    for user in users:
        logger.info(f"Notification. {user['name']}: {user['message']}")
        if user['message'] != 'none':
            message = {
                'users': [user['id']],
                'text': messages[user['message']],
                'access_token': os.environ.get('LINE_ACCESS_TOKEN')
            }
            logger.info(json.dumps(message, ensure_ascii=False, indent=3))
            topic.publish(Message=json.dumps(message))


if __name__ == '__main__':
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    handle({'time': '2017-12-28T22:45:00Z'}, None)
