import mysql.connector
from model import SpreadsheetData
import copy
from log.logger import setup_logger

logger = setup_logger(__name__)


def connect_to_mysql_server(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name, user=user_name, passwd=user_password
        )
        logger.debug("MySQL Database connection successful")
    except Exception as err:
        logger.error(f"Error: '{err}'")
    return connection


def create_or_check_database(connection, db_name):
    query = "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET 'utf8'".format(
        db_name
    )
    execute_query(
        connection,
        query,
        success_message="Create DB or already exists",
        error_message="Failed creating database",
    )


def create_or_check_table(connection, table_name):
    query = """
    CREATE TABLE IF NOT EXISTS {} (
        league VARCHAR(50),
        team_name VARCHAR(50),
        handle_name VARCHAR(50),
        role VARCHAR(50),
        first_name VARCHAR(50) NOT NULL,
        family_name VARCHAR(50) NOT NULL,
        end_date INT(4) NOT NULL,
        resident VARCHAR(50),
        roster_status VARCHAR(50),
        team_tag VARCHAR(50),
        team_contact_info VARCHAR(50),
        PRIMARY KEY (first_name, family_name)
    )
    """.format(
        table_name
    )
    execute_query(
        connection,
        query,
        success_message="Create table or already exists",
        error_message="Failed creating table",
    )


def execute_query(
    connection, query, success_message: str = None, error_message: str = "Error"
):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        if success_message is not None:
            logger.debug(success_message)
    except Exception as err:
        logger.error("{}: '{}'".format(error_message, err))
        exit(1)


def insert_data_to_db(connection, table_name, data_list):
    cursor = connection.cursor()
    query = """ INSERT INTO `{}`(
        `league`, `team_name`, `handle_name`,`role`,`first_name`,`family_name`,
        `end_date`,`resident`,`roster_status`,`team_tag`,`team_contact_info`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """.format(
        table_name
    )
    try:
        # insert用に最適化されたexecutemanyメソッドを使用
        cursor.executemany(query, [data.values() for data in data_list])
        connection.commit()
        if data_list != []:
            logger.debug("Success writing table")
    except Exception as err:
        logger.error("Error: '{}'".format(err))
        exit(1)


# DBのテーブルのデータを読み込む
def read_data_from_db(connection, table_name):
    cursor = connection.cursor()
    query = "SELECT * FROM {}".format(table_name)
    try:
        cursor.execute(query)
        data_list_from_db = [SpreadsheetData(*row) for row in cursor.fetchall()]
        logger.debug("Success reading table")
        return data_list_from_db
    except Exception as err:
        logger.error("Failed reading table: '{}'".format(err))
        exit(1)


# すでに存在するレコードを更新する
def update_data_to_db(connection, table_name, data_list: list[SpreadsheetData]):
    for data in data_list:
        execute_query(
            connection,
            """UPDATE {} SET league = '{}', team_name = '{}', handle_name = '{}',
                role = '{}', end_date = {}, resident = '{}', roster_status = '{}',
                team_tag = '{}', team_contact_info = '{}' where first_name='{}'
                AND family_name='{}'""".format(
                table_name,
                data.league,
                data.team_name,
                data.handle_name,
                data.role,
                data.end_date,
                data.resident,
                data.roster_status,
                data.team_tag,
                data.team_contact_info,
                data.first_name,
                data.family_name,
            ),
            success_message="Success updating table",
            error_message="Failed updating table",
        )


# レコードの削除を行う
def delete_data_from_db(connection, table_name, data_list):
    for data in data_list:
        execute_query(
            connection,
            "DELETE FROM {} WHERE first_name = '{}' AND family_name= '{}'".format(
                table_name, data.first_name, data.family_name
            ),
            success_message="Success deleting record",
            error_message="Failed deleting record",
        )


def show_data_list(data_list):
    if data_list == []:
        logger.debug("No data in this list")
        return
    for data in data_list:
        logger.debug(data.values())


# リストを2つ受け取り、差分を更新/追加/削除済みの3つのリストに分けて返す
def diff_lists_from_data_lists(
    data_list_new: list[SpreadsheetData], data_list_old: list[SpreadsheetData]
):
    if data_list_new == [] or data_list_old == []:
        logger.warning("No data in old|new list")
        return ([], [], [], [])
    # それぞれのリストをfirst_nameでソート
    data_list_new.sort(key=lambda x: x.first_name)
    data_list_old.sort(key=lambda x: x.first_name)
    # 既存のDBからは主キー(first_name, family_name)が重複することはない
    # しかしSpreadsheetから取得したdata_list_newでは重複することがあるので、事前に取り除く
    # 将来的にはDBを正規化することが必要だが、とりあえずend_dateが長いほうを残すことにする
    # 処理としてはupdateになるので、L378以降のチーム名の変更が表示される
    data_list_update_old = []
    data_list_update_new = []
    data_list_added = []
    data_list_removed = []
    # 重複を除去
    for newd1 in data_list_new:
        for newd2 in data_list_new:
            # 同じ名前のデータが複数存在する場合
            if (
                newd1.first_name == newd2.first_name
                and newd1.family_name == newd2.family_name
                and newd1 != newd2
            ):
                if newd1.end_date >= newd2.end_date:
                    data_list_new.remove(newd2)
                else:
                    data_list_new.remove(newd1)
    data_list_added.extend(copy.deepcopy(data_list_new))
    data_list_removed.extend(copy.deepcopy(data_list_old))
    for new_data in data_list_new:
        for old_data in data_list_old:
            # もし同じ名前のデータがあったら
            if (
                new_data.first_name == old_data.first_name
                and new_data.family_name == old_data.family_name
            ):
                # それぞれのデータを比較
                if new_data != old_data:
                    data_list_update_old.append(old_data)
                    data_list_update_new.append(new_data)
                data_list_added.remove(new_data)
                data_list_removed.remove(old_data)
    # ログに出力
    logger.debug("list_update_old")
    show_data_list(data_list_update_old)
    logger.debug("list_update_new")
    show_data_list(data_list_update_new)
    logger.debug("list_removed")
    show_data_list(data_list_removed)
    logger.debug("list_added")
    show_data_list(data_list_added)
    return (
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    )
