# VCTGlobalContract
VCTGlobalContractのスクレイピングを行うプログラム

# Usage and Options
1. `.env`を作成
- `HOST_NAME`: MySQLのホスト名
- `USER_NAME`: MySQLのユーザ名
- `PASSWORD`: MySQLのパスワード
- `WEBHOOK_URL`: DiscordのWebhook URL
- `WEBHOOK_URL_SIMULATE`: シミュレーション時のDiscordのWebhook URL(任意)

`.env.example`を参考にしてください。

2. `python3 scraping.py`を実行
```
$ python3 scraping.py
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

`--simulate`をつけると、DBへの書き込みを行わずに、`WEBHOOK_URL_SIMULATE`で指定したURLへの投稿のみを行います。
