# LINE BOT for Rainy Day
毎朝、雨が降りそうな日に傘を持っていくようメッセージを送ってくれるLINE BOT。

## 初めに
PythonやAWSの勉強のため、開発中。  
さくらVPSでRuby, Sinatraで開発済のものをPythonとAWSで更改中。

## 利用方法
一般公開はしておりません。

## アプリケーション構成
AWS LambdaとAWS API Gatewayで構築。
以下の4つのlambda関数から構成されている。

- **get_weather**  
天気予報を取得するlambda関数。起動タイミングは毎朝6:00(JST)頃。
＜処理＞
    1. インターネットから天気予報情報を取得してRDSへ天気情報を保存。
    1. 天気情報とユーザ情報から誰にどのタイミングでどんなメッセージを通知するかを表す予定情報を作成し、RDSへ保存。また、yamlファイルでS3に保存。
- **push_notice**  
起動された時刻と予定情報から、LINEでメッセージを送る相手と内容を判定しプッシュ通知を送る。
- **line_bot**  
ユーザ登録・解除、通知時刻、通知条件（降水確率）をLINEトーク上で行う。
- **sync_table**  
DynamoDBに保存されたユーザ情報をPostgreSQLに還元する。

## インフラ構成
前述の通り、AWS LambdaとAWS API Gatewaで構成されている。
構成図は以下の通り。

![AWS構成](https://github.com/juv-shun/forecast2/blob/readme_img/images/aws_constructure.gif "AWS構成")
