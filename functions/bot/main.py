import os
import json
import hashlib
import hmac
import base64
import logging

from weatherbot import WeatherBot

logger = logging.getLogger()
logger.setLevel(logging.INFO)

weather_bot = WeatherBot(os.environ.get('CHANNEL_ACCESS_TOKEN'))


def handle(event, context):
    if event == {'dummy': True}:
        logger.info('dummy.')
        return {
            "statusCode": 200,
            "headers": {},
            "body": "Dummy request."
        }

    if not verify_signature(event):
        logger.warning('Invalid signature.')
        return {
            "statusCode": 200,
            "headers": {},
            "body": "Invalid signature."
        }

    body = json.loads(event['body'])
    for event in body['events']:
        weather_bot.reply(event)

    return {
        "statusCode": 200,
        "headers": {},
        "body": "ok"
    }


def verify_signature(request):
    line_sign = request['headers']['X-Line-Signature']
    body = request['body']

    hash = hmac.new(os.environ.get('CHANNEL_SECRET').encode('utf-8'),
                    body.encode('utf-8'), hashlib.sha256).digest()

    return base64.b64encode(hash) == line_sign.encode('utf-8')


if __name__ == '__main__':
    with open('test/full_event.json', 'r') as rf:
        event = json.load(rf)
    res = handle(event, None)
    print(res)
