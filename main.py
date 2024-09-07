from __future__ import annotations
import os
import sys
import requests.packages.urllib3.util.connection as urllib3_cn
import socket
from dotenv import load_dotenv
from utils.utils import setup_logger
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

# from scraping.simulate import main_simulate
from scraping.spreadsheet import get_spreadsheet_data_list
from message.message_creator import create_message_list
from discord_utils.discord_message import post_message_list

logger = setup_logger(__name__)


# ソケットの通信をIPv4のみに制限
def allowed_gai_family4():
    return socket.AF_INET


urllib3_cn.allowed_gai_family = allowed_gai_family4
TARGET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmmWiBmMMD43m5VtZq54nKlmj0ZtythsA1qCpegwx-iRptx2HEsG0T3cQlG1r2AIiKxBWnaurJZQ9Q/pubhtml#"
DB_NAME = "VCTContractsDB"
TABLE_NAME = "VCTContractsTable"


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
    message_list = create_message_list(
        WEBHOOK_URL,
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    )
    post_message_list(WEBHOOK_URL, message_list)

    # MySQLサーバーとの接続を切断
    connection.close()


if __name__ == "__main__":
    setup_logger()
    if len(sys.argv) >= 2 and sys.argv[1] == "--simulate":
        logger.debug("---START simulation mode---")
        # main_simulate()
        logger.debug("---END simulation mode---")
    else:
        main()
