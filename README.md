# LINE BOT for Rainy Day
毎朝、雨が降りそうな日に傘を持っていくようメッセージを送ってくれるLINE BOT。

## 利用方法
一般公開はしておりません。

## アプリケーション構成
AWS LambdaとAWS API Gatewayで構築。
以下の3つのlambda関数から構成されている。

- **weather_manager**
天気予報を取得し、登録ユーザ各々に対する送信メッセージを決める。
- **notificator**
lambda起動時刻とユーザが設定した送信時刻が一致した場合、LINEメッセージを送信する。
- **linebot**
ユーザ登録・解除、通知時刻、通知条件（降水確率）をLINEトーク上で行う。


## How to run on your local

### Dynamo DB local setting

```sh
$ sls dynamodb install
$ sls dynamodb start &
$ npx dynamodb-admin &
```

### Environment Variables

```sh
export DYNAMODB_TABLE=dummy
export S3_BUCKET=dummy
export S3_MESSAGE_OBJ_KEY=dummy
export LINE_ACCESS_TOKEN=dummy
export LINE_CHANNEL_SECRET=dummy
export AWS_ACCOUNT_ID=dummy
```

### weather_manager, notificator

```sh
$ sls invoke local -f weather_manager -e IS_LOCAL=true
$ sls invoke local -f notificator -d '{"time": "2021-05-26T23:31:00Z"}' -e IS_LOCAL=true
```

### linebot

```sh
$ sls offline
$ curl -H 'x-line-signature: dummy' http://localhost:3000/ -d @src/linebot/testdata.json
```
