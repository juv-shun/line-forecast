import os
import json
import hashlib
import hmac
import base64
from weatherbot import WeatherBot
from logging import (getLogger, INFO)

CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
ENCODING = 'utf-8'

weather_bot = WeatherBot(CHANNEL_ACCESS_TOKEN)
logger = getLogger()
logger.setLevel(INFO)


def handle(event, context):
    if event == {'dummy': True}:
        logger.info('dummy.')
        return 'Dummy request.'

    if not verify_signature(event):
        logger.warning('Invalid signature.')
        return 'WARNING'

    body = json.loads(event['body'])
    for event in body['events']:
        weather_bot.reply(event)

    return 'OK'


def verify_signature(event):
    hash = hmac.new(CHANNEL_SECRET.encode(ENCODING),
                    event['body'].encode(ENCODING),
                    hashlib.sha256).digest()
    h_signature = event['headers']['X-Line-Signature'].encode(ENCODING)
    b_signature = base64.b64encode(hash)

    if b_signature == h_signature:
        return True
    else:
        return False


if __name__ == '__main__':
    with open('test/full_event.json', 'r') as rf:
        event = json.load(rf)
    res = handle(event, None)
    print(res)
