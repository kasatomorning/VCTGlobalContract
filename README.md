# VCTGlobalContract
VCTGlobalContractのスクレイピングを行うプログラムです。

MySQLにデータを保存し、追加、更新、削除があった場合にDiscordに通知します。

# Usage and Options
1. `.env`を作成
- `HOST_NAME`: MySQLのホスト名
- `USER_NAME`: MySQLのユーザ名
- `PASSWORD`: MySQLのパスワード
- `WEBHOOK_URL`: DiscordのWebhook URL
- `WEBHOOK_URL_TEST`: テスト時のDiscordのWebhook URL

`.env.example`を参考にしてください。

2. `python3 main.py`を実行
```
$ python3 main.py
MySQL Database connection successful
Create DB or already exists
Create table or already exists
Success reading table
list_update_old
No data in this list
list_update_new
No data in this list
list_removed
No data in this list
list_added
['PACIFIC', 'TEST ESPORTS', 'TEST', 'ACTIVE PLAYER', 'TAROU', 'YAMADA', 2026, 'RESIDENT', 'Active', 'TE', '']
Success writing table
{"username": "VCTContracts\u544a\u77e5", "embeds": [{"color": 7935, "image": {"url": ""}, "title": "TEST(TAROU YAMADA, ACTIVE PLAYER) joined TEST ESPORTS"}]}
Success post request
```

`--verify`をつけると、既存のテーブルを更新せずに`WEBHOOK_URL_TEST`で指定したURLへの投稿のみを行います。

# Sample
![alt text](misc/image.png)