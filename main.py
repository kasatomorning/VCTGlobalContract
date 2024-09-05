from __future__ import annotations
import requests
from mysql.connector import Error
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
import time
import sys
import requests.packages.urllib3.util.connection as urllib3_cn
import socket
from log.logger import setup_logger
from db.db_access import (
    connect_to_mysql_server,
    create_or_check_database,
    execute_query,
    create_or_check_table,
    read_data_from_db,
    diff_lists_from_data_lists,
    update_data_to_db,
    delete_data_from_db,
    insert_data_to_db,
)
from scraping.simulate import main_simulate
from model.models import Color
from scraping.scraping import get_spreadsheet_data_list

logger = setup_logger(__name__)


# ソケットの通信をIPv4のみに制限
def allowed_gai_family4():
    return socket.AF_INET


urllib3_cn.allowed_gai_family = allowed_gai_family4
TARGET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmmWiBmMMD43m5VtZq54nKlmj0ZtythsA1qCpegwx-iRptx2HEsG0T3cQlG1r2AIiKxBWnaurJZQ9Q/pubhtml#"
COLUMN_NUM = 11
DB_NAME = "VCTContractsDB"
TABLE_NAME = "VCTContractsTable"


# Discordのリクエスト, jsonにして送信する
class DiscordRequestMainContent:
    def __init__(self, color: Color, image_url, title) -> None:
        self.username = "VCTContracts告知"
        self.embeds = [
            {
                "color": color.value,
                "image": {"url": image_url},
                "title": title,
            }
        ]


def post_message_list(webhook_url, show_data: list[DiscordRequestMainContent]):
    headers = {"Content-Type": "application/json"}
    # リストが空のときはリクエストを送らない
    if show_data == []:
        logger.debug("No POST data...Finish!")
        return
    for data in show_data:
        main_content = json.dumps(data.__dict__)
        logger.debug(main_content)
        try:
            response = requests.post(
                url=webhook_url, headers=headers, data=main_content, timeout=10
            )
            response.raise_for_status()
            logger.debug("Success post request")
            # 大量の更新があった場合でも429が返ってこないようにする
            time.sleep(3)
        except Error as err:
            logger.warning("Failed post request: '{}'".format(err))
            exit(1)


# 差分を取り、team_name, end_date, roster_status, roleの変更のみ告知する
def compare_and_post_diff_list(
    webhook_url,
    data_list_update_old,
    data_list_update_new,
    data_list_added,
    data_list_removed,
):
    message_list: list[DiscordRequestMainContent] = []

    # updateされたデータをmessage_listに追加
    for index in range(len(data_list_update_new)):
        if data_list_update_new[index] == data_list_update_old[index]:
            break
        data_new = data_list_update_new[index]
        data_old = data_list_update_old[index]
        title_str = ""
        if data_new.team_name != data_old.team_name:
            title_str = "{}({} {}, {}, ex-{}) joined {}".format(
                data_new.handle_name,
                data_new.first_name,
                data_new.family_name,
                data_new.role,
                data_old.team_name,
                data_new.team_name,
            )
        elif data_new.end_date != data_old.end_date:
            title_str = (
                "The end date of {}({} {}, {} in {}) was changed from {} to {}".format(
                    data_new.handle_name,
                    data_new.first_name,
                    data_new.family_name,
                    data_new.role,
                    data_new.team_name,
                    data_old.end_date,
                    data_new.end_date,
                )
            )
        elif data_new.roster_status != data_old.roster_status:
            title_str = "{}({} {}, {} in {}) is {} now".format(
                data_new.handle_name,
                data_new.first_name,
                data_new.family_name,
                data_new.role,
                data_new.team_name,
                data_new.roster_status,
            )
        elif data_new.role != data_old.role:
            title_str = "{}({} {} in {}) changed role from {} to {}".format(
                data_new.handle_name,
                data_new.first_name,
                data_new.family_name,
                data_new.team_name,
                data_old.role,
                data_new.role,
            )
        if title_str != "":
            image_url = get_picture_from_liquipedia(data_new.handle_name)
            message_list.append(
                DiscordRequestMainContent(Color.UPDATE, image_url, title_str)
            )

    # 削除されたデータをmessage_listに追加
    for data in data_list_removed:
        message_list.append(
            DiscordRequestMainContent(
                color=Color.REMOVED,
                image_url=get_picture_from_liquipedia(data.handle_name),
                title="{}({} {}, {}) was removed from {}".format(
                    data.handle_name,
                    data.first_name,
                    data.family_name,
                    data.role,
                    data.team_name,
                ),
            )
        )

    # 追加されたデータをmessage_listに追加
    for data in data_list_added:
        message_list.append(
            DiscordRequestMainContent(
                color=Color.ADDED,
                image_url=get_picture_from_liquipedia(data.handle_name),
                title="{}({} {}, {}) joined {}".format(
                    data.handle_name,
                    data.first_name,
                    data.family_name,
                    data.role,
                    data.team_name,
                ),
            )
        )
    post_message_list(webhook_url, message_list)


def get_picture_from_liquipedia(player_name):
    try:
        request_url = "https://liquipedia.net/valorant/{}".format(player_name)
        response = requests.get(request_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, features="html.parser")
        image_url = soup.find("meta", attrs={"property": "og:image"})["content"]
        # もしデフォルトの写真の場合は空文字列を返す
        if "facebook-image.png" in image_url:
            return ""
        return image_url
    except Exception as e:
        # liquipediaにアクセスできない場合・ユーザーが存在しない場合などは空文字列を返す
        logger.debug(e)
        return ""


def main():
    # 環境変数を読み込む
    load_dotenv()
    HOST_NAME = os.getenv("HOST_NAME")
    USER_NAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    # スプレッドシートのpubhtmlのデータを取得
    data_list_from_spreadsheet = get_spreadsheet_data_list(TARGET_URL)
    # MySQLサーバーに接続
    connection = connect_to_mysql_server(HOST_NAME, USER_NAME, PASSWORD)
    # DBを作成|存在確認
    create_or_check_database(connection, DB_NAME)
    # DBを選択
    execute_query(connection, "USE {}".format(DB_NAME))
    # テーブルを作成|存在確認
    create_or_check_table(connection, TABLE_NAME)

    # テーブルのデータを表示
    data_list_from_db = read_data_from_db(connection, TABLE_NAME)
    # DBとスプレッドシートのデータを比較し、差分のリストを取得
    (
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    ) = diff_lists_from_data_lists(data_list_from_spreadsheet, data_list_from_db)

    # DBの更新、追加、削除
    update_data_to_db(connection, TABLE_NAME, data_list_update_new)
    delete_data_from_db(connection, TABLE_NAME, data_list_removed)
    insert_data_to_db(connection, TABLE_NAME, data_list_added)

    # WEBHOOKを利用してdiffを送信
    compare_and_post_diff_list(
        WEBHOOK_URL,
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    )
    # MySQLサーバーとの接続を切断
    connection.close()


if __name__ == "__main__":
    setup_logger()
    if len(sys.argv) >= 2 and sys.argv[1] == "--simulate":
        logger.debug("---START simulation mode---")
        main_simulate()
        logger.debug("---END simulation mode---")
    else:
        main()
