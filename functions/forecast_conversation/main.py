import os
import json
import hashlib
import hmac
import base64

CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
ENCODING = 'utf-8'


def handle(event, context):
    if is_dummy(event):
        return 'Dummy requests.'

    if not verify_signature(event):
        return 'Invalid signature.'

    response(json.loads(event['body']))

    return 'OK'


def is_dummy(event):
    return 'dummy' in event.keys() and event['dummy'] is True


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


def response(req):
    print(req)


if __name__ == '__main__':
    handle(None, None)
