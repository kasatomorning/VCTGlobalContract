from __future__ import annotations
import conf.global_values as g
import sys

import urllib3.util.connection as urllib3_cn
import socket
from conf.settings import load_env
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

from scraping.spreadsheet import get_spreadsheet_data_list
from message.message_creator import create_message_list


# ソケットの通信をIPv4のみに制限
def allowed_gai_family4():
    return socket.AF_INET


def main(table_name: str, webhook_url: str):
    # スプレッドシートのpubhtmlのデータを取得
    data_list_from_spreadsheet = get_spreadsheet_data_list(g.TARGET_URL)
    # MySQLサーバーに接続
    connection = connect_to_mysql_server(g.HOST_NAME, g.USER_NAME, g.PASSWORD)
    # DBを作成|存在確認
    create_or_check_database(connection, g.DB_NAME)
    # DBを選択
    execute_query(connection, "USE {}".format(g.DB_NAME))
    # テーブルを作成|存在確認
    create_or_check_table(connection, table_name)

    # テーブルのデータを表示
    data_list_from_db = read_data_from_db(connection, table_name)
    # DBとスプレッドシートのデータを比較し、差分のリストを取得
    (
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    ) = diff_lists_from_data_lists(data_list_from_spreadsheet, data_list_from_db)

    # DBの更新、追加、削除
    update_data_to_db(connection, table_name, data_list_update_new)
    delete_data_from_db(connection, table_name, data_list_removed)
    insert_data_to_db(connection, table_name, data_list_added)

    # WEBHOOKを利用してdiffを送信
    message_list = create_message_list(
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
        webhook_url=webhook_url,
    )
    for message in message_list:
        message.post()

    # MySQLサーバーとの接続を切断
    connection.close()


def main_verify():
    """
    本当にDBを更新できるかどうかを試すための関数
    VCTContractsTableSimulateにVCTContractsTableのデータをコピーし更新
    WEBHOOK_URL_SIMULATEに差分を送信する
    """
    # 環境変数を読み込む
    load_env()

    # スプレッドシートのpubhtmlのデータを取得
    data_list_from_spreadsheet = get_spreadsheet_data_list(g.TARGET_URL)

    # MySQLサーバーに接続
    connection = connect_to_mysql_server(g.HOST_NAME, g.USER_NAME, g.PASSWORD)
    # DBを作成|存在確認
    create_or_check_database(connection, g.DB_NAME)
    # DBを選択
    execute_query(connection, "USE {}".format(g.DB_NAME))
    # テーブルを作成|存在確認
    create_or_check_table(connection, g.TABLE_NAME_TEST)
    # 既存のデータを削除
    execute_query(
        connection,
        "DELETE FROM {}".format(g.TABLE_NAME_TEST),
        success_message="Success reset table data",
        error_message="Failed reset table data",
    )
    # 実際のテーブルのデータをコピー
    execute_query(
        connection,
        "INSERT INTO {} SELECT * FROM {};".format(g.TABLE_NAME_TEST, g.TABLE_NAME),
        success_message="Success copying table",
        error_message="Failed copying table",
    )
    # テーブルのデータを表示
    data_list_from_db = read_data_from_db(connection, g.TABLE_NAME_TEST)
    # DBとスプレッドシートのデータを比較し、差分のリストを取得
    (
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    ) = diff_lists_from_data_lists(data_list_from_spreadsheet, data_list_from_db)

    # DBの更新、追加、削除
    update_data_to_db(connection, g.TABLE_NAME_TEST, data_list_update_new)
    delete_data_from_db(connection, g.TABLE_NAME_TEST, data_list_removed)
    insert_data_to_db(connection, g.TABLE_NAME_TEST, data_list_added)
    # WEBHOOKを利用してdiffを送信
    message_list = create_message_list(
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
        webhook_url=g.WEBHOOK_URL,
    )
    for message in message_list:
        message.post()

    # MySQLサーバーとの接続を切断
    connection.close()


if __name__ == "__main__":
    logger = setup_logger(__name__)
    load_env()
    urllib3_cn.allowed_gai_family = allowed_gai_family4
    try:
        if len(sys.argv) >= 2 and sys.argv[1] == "--verify":
            logger.debug("---START verify mode---")
            main_verify()
            logger.debug("---END verify mode---")
        elif len(sys.argv) >= 2 and sys.argv[1] == "--test":
            logger.debug("---START test mode---")
            print("Table name: ", g.TABLE_NAME_TEST)
            print("Webhook URL: ", g.WEBHOOK_URL_TEST)
            main(g.TABLE_NAME_TEST, g.WEBHOOK_URL_TEST)
            logger.debug("---END test mode---")
        else:
            main(g.TABLE_NAME, g.WEBHOOK_URL)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
