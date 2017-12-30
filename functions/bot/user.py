import os
import boto3
from logging import getLogger, DEBUG

TABLE_NAME = os.environ.get('TABLE_NAME')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

logger = getLogger(__name__)
logger.setLevel(DEBUG)


class User():
    __columns = {'id', 'name', 'timing', 'percent',
                 'area', 'active', 'talk_status', 'message'}

    @classmethod
    def find(cls, user_id):
        res = table.get_item(Key={'id': user_id})
        if 'Item' in res:
            if res['Item'].keys() == cls.__columns:
                return User(id=res['Item']['id'],
                            name=res['Item']['name'],
                            timing=res['Item']['timing'],
                            percent=res['Item']['percent'],
                            area=res['Item']['area'],
                            active=res['Item']['active'],
                            talk_status=res['Item']['talk_status'],
                            message=res['Item']['message'])
            else:
                raise ValueError
        else:
            return None

    def __init__(self, id, name, timing='06:15', percent=40, area='東京',
                 active=True, setting_status='Wait', talk_status='Wait',
                 message='none'):
        self.id = id
        self.name = name
        self.timing = timing
        self.percent = percent
        self.area = area
        self.active = active
        self.talk_status = talk_status
        self.message = message

    def save(self):
        item = {'id': self.id,
                'name': self.name,
                'timing': self.timing,
                'percent': self.percent,
                'area': self.area,
                'active': self.active,
                'talk_status': self.talk_status,
                'message': self.message}
        table.put_item(Item=item)
