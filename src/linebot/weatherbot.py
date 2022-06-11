import json
import os
import logging

import boto3
from linebot import LineBotApi
from linebot.models import TextSendMessage

from .user import User

S3_BUCKET = os.environ["S3_BUCKET"]
S3_MESSAGE_OBJ_KEY = os.environ["S3_MESSAGE_OBJ_KEY"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def load_message():
    s3 = boto3.resource("s3")
    obj = s3.Object(S3_BUCKET, S3_MESSAGE_OBJ_KEY)
    message = json.load(obj.get()["Body"])
    return message["reaction"]


class WeatherBot(LineBotApi):
    __timing_choices = {
        "A": "06:15",
        "B": "06:30",
        "C": "06:45",
        "D": "07:00",
        "E": "07:15",
        "F": "07:30",
        "G": "07:45",
        "H": "08:00",
        "I": "08:15",
        "J": "08:30",
        "K": "08:45",
    }
    __percent_choices = {"A": 30, "B": 40, "C": 50}
    __messages = load_message()

    def __init__(self, channel_access_token):
        super().__init__(channel_access_token)

    def reply(self, event):
        user_id = event["source"]["userId"]

        # テキストが送信されてきた場合の対応
        if event["type"] == "message" and event["message"]["type"] == "text":
            logger.info(
                "Input type: message, Input message: %s" % event["message"]["text"]
            )
            result = self.__react(user_id=user_id, method=event["message"]["text"])

        # フォローされた場合の対応
        elif event["type"] == "follow":
            logger.info("Input type: follow")
            result = self.__react(user_id=user_id, method="登録")

        # フォローが外された場合の対応
        elif event["type"] == "unfollow":
            logger.info("Input type: unfollow")
            result = self.__react(user_id=user_id, method="登録解除")

        # 対応結果によりメッセージを生成
        message = self.__generate_message(result, user_id)
        logger.info("Reply message: %s" % message)

        # メッセージ送信
        self.reply_message(
            messages=TextSendMessage(text=message), reply_token=event["replyToken"]
        )

    def __react(self, user_id, method):
        user = User.find(user_id)

        if method == "登録":
            return self.__register(user, user_id)

        elif method == "登録解除":
            return self.__unregister(user)

        elif method == "ヘルプ":
            return self.__show_help()

        elif method == "設定表示":
            return self.__show_setting(user)

        elif method == "通知時刻変更":
            return self.__show_timing_choices(user)

        elif method == "降水確率変更":
            return self.__show_percent_choices(user)

        elif user is not None and user.talk_status == "WaitTiming":
            return self.__change_timing(user, method)

        elif user is not None and user.talk_status == "WaitPercent":
            return self.__change_percent(user, method)

        else:
            return self.__reply_unknown()

    def __register(self, user, user_id):
        if user is None:
            profile = self.get_profile(user_id)
            user = User(id=profile.user_id, name=profile.display_name)
            user.save()
            return "register", "done"
        elif not user.active:
            user.active = True
            user.save()
            return "register", "redone"
        else:
            return "register", "duplicate"

    def __unregister(self, user):
        if user is None or not user.active:
            return "unregister", "already"
        else:
            user.active = False
            user.talk_status = "Wait"
            user.save()
            return "unregister", "done"

    def __show_help(self):
        return "help"

    def __show_setting(self, user):
        if user is None or not user.active:
            return "setting", "not_active"
        else:
            return "setting", "view"

    def __show_timing_choices(self, user):
        if user is None or not user.active:
            return "setting", "not_active"
        else:
            user.talk_status = "WaitTiming"
            user.save()
            return "setting", "time", "question"

    def __show_percent_choices(self, user):
        if user is None or not user.active:
            return "setting", "not_active"
        else:
            user.talk_status = "WaitPercent"
            user.save()
            return "setting", "percent", "question"

    def __change_timing(self, user, answer):
        if user is None or not user.active:
            return "setting", "not_active"
        elif answer in self.__class__.__timing_choices.keys():
            user.timing = self.__class__.__timing_choices[answer]
            user.talk_status = "Wait"
            user.save()
            return "setting", "time", "done"
        else:
            return "setting", "time", "invalid"

    def __change_percent(self, user, answer):
        if user is None or not user.active:
            return "setting", "not_active"
        elif answer in self.__class__.__percent_choices.keys():
            user.percent = self.__class__.__percent_choices[answer]
            user.talk_status = "Wait"
            user.save()
            return "setting", "percent", "done"
        else:
            return "setting", "percent", "invalid"

    def __reply_unknown(self):
        return "none"

    def __generate_message(self, keys, user_id):
        # メッセージテンプレートを取得
        if isinstance(keys, str):
            template = self.__class__.__messages[keys]
        elif isinstance(keys, tuple) and len(keys) == 2:
            template = self.__class__.__messages[keys[0]][keys[1]]
        elif isinstance(keys, tuple) and len(keys) == 3:
            template = self.__class__.__messages[keys[0]][keys[1]][keys[2]]
        else:
            raise ValueError

        # テンプレートの変数部分を変換
        user = User.find(user_id)
        if template is not None and user is not None:
            message = template.replace("$time$", user.timing)
            message = message.replace("$percent$", str(user.percent))
        else:
            message = template

        return message
