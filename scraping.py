from __future__ import annotations
import requests
import mysql.connector
from mysql.connector import Error
from bs4 import BeautifulSoup
from enum import Enum
import json
import os
from dotenv import load_dotenv
import copy


target_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmmWiBmMMD43m5VtZq54nKlmj0ZtythsA1qCpegwx-iRptx2HEsG0T3cQlG1r2AIiKxBWnaurJZQ9Q/pubhtml#"


class League(Enum):
    PACIFIC = "PACIFIC"
    EMEA = "EMEA"
    AMERICAS = "AMERICAS"


class SpreadsheetData:
    league: League
    team_name: str
    handle_name: str
    role: str
    first_name: str
    family_name: str
    end_date: int
    resident: str
    roster_status: str
    team_tag: str
    team_contact_info: str

    def __init__(
        self,
        league: League,
        team_name: str,
        handle_name: str,
        role: str,
        first_name: str,
        family_name: str,
        end_date: str,
        resident: str,
        roster_status: str,
        team_tag: str,
        team_contact_info: str,
    ):
        self.league = league
        self.team_name = team_name
        self.handle_name = handle_name
        self.role = role
        self.first_name = first_name
        self.family_name = family_name
        self.end_date = int(end_date) if end_date != "" else 0
        self.resident = resident
        self.roster_status = roster_status
        self.team_tag = team_tag
        self.team_contact_info = team_contact_info

    def __eq__(self, other: SpreadsheetData):
        return (
            self.league == other.league
            and self.team_name == other.team_name
            and self.handle_name == other.handle_name
            and self.role == other.role
            and self.first_name == other.first_name
            and self.family_name == other.family_name
            and self.end_date == other.end_date
            and self.resident == other.resident
            and self.roster_status == other.roster_status
            and self.team_tag == other.team_tag
            and self.team_contact_info == other.team_contact_info
        )

    def __ne__(self, other: SpreadsheetData):
        return not self.__eq__(other)

    def values(self):
        return [
            self.league,
            self.team_name,
            self.handle_name,
            self.role,
            self.first_name,
            self.family_name,
            self.end_date,
            self.resident,
            self.roster_status,
            self.team_tag,
            self.team_contact_info,
        ]


def get_spreadsheet_data_list(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tr_element = soup.find_all("tr")
    data_list = []
    for i in tr_element:
        texts = i.findAll("td")
        text_list = []
        for j in texts:
            text_list.append(j.text)
        # 空行・リーグ名が不正な行・選手名が空の行は無視
        if (
            len(text_list) == 0
            or text_list[0] not in [league.value for league in League]
            or text_list[4] == ""
            or text_list[5] == ""
        ):
            continue
        data = SpreadsheetData(*text_list)
        data_list.append(data)
    return data_list


def connect_to_mysql_server(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name, user=user_name, passwd=user_password
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
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
            print(success_message)
    except Error as err:
        print("{}: '{}'".format(error_message, err))
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
        print("Success writing table")
    except Error as err:
        print("Error: '{}'".format(err))
        exit(1)


# DBのテーブルのデータを読み込む
def read_data_from_db(connection, table_name):
    cursor = connection.cursor()
    query = "SELECT * FROM {}".format(table_name)
    try:
        cursor.execute(query)
        data_list_from_db = [SpreadsheetData(*row) for row in cursor.fetchall()]
        print("Success reading table")
        return data_list_from_db
    except Error as err:
        print("Failed reading table: '{}'".format(err))
        exit(1)


# すでに存在するレコードを更新する
def update_data_to_db(connection, table_name, data_list: list[SpreadsheetData]):
    for data in data_list:
        execute_query(
            connection,
            """UPDATE {} SET league = '{}', team_name = '{}', handle_name = '{}',
                role = '{}', end_date = {}, resident = '{}', roster_status = '{}',
                team_tag = '{}', team_contact_info = '{}'""".format(
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
        print("No data in this list")
        return
    for data in data_list:
        print(data.values())


# リストを2つ受け取り、差分を更新/追加/削除済みの3つのリストに分けて返す
def diff_lists_from_data_lists(
    data_list_new: list[SpreadsheetData], data_list_old: list[SpreadsheetData]
):
    if data_list_new == [] and data_list_old == []:
        print("No data in either list")
        return False
    # それぞれのリストをfirst_nameでソート
    data_list_new.sort(key=lambda x: x.first_name)
    data_list_old.sort(key=lambda x: x.first_name)
    data_list_added = copy.deepcopy(data_list_new)
    data_list_removed = copy.deepcopy(data_list_old)
    data_list_update = []
    for new_data in data_list_new:
        for old_data in data_list_old:
            # もし同じ名前のデータがあったら
            if (
                new_data.first_name == old_data.first_name
                and new_data.family_name == old_data.family_name
            ):
                # それぞれのデータを比較
                if new_data != old_data:
                    data_list_update.append(new_data)
                data_list_added.remove(new_data)
                data_list_removed.remove(old_data)
    return (data_list_update, data_list_added, data_list_removed)


def post_str_list_request(webhook_url, show_data: list[str]):
    headers = {"Content-Type": "application/json"}
    # リストが空のときはリクエストを送らない
    if show_data == []:
        print("No data in this list")
        return
    post_data = {"content": "\n".join(show_data)}
    try:
        response = requests.post(
            webhook_url, headers=headers, data=json.dumps(post_data)
        )
        response.raise_for_status()
        print("Success post request")
    except Error as err:
        print("Failed post request: '{}'".format(err))
        exit(1)


def post_diff_list(webhook_url, data_list_update, data_list_added, data_list_removed):
    message_list: list[str] = []
    for data in data_list_update:
        message_list.append("Update: {}".format(data.values()))
    for data in data_list_added:
        message_list.append(
            "New Roaster!\n{}({} {},{}) joined {}".format(
                data.handle_name,
                data.first_name,
                data.family_name,
                data.role,
                data.team_name,
            )
        )
    for data in data_list_removed:
        message_list.append(
            "{}({} {},{}) was removed from {}".format(
                data.handle_name,
                data.first_name,
                data.family_name,
                data.role,
                data.team_name,
            )
        )
    post_str_list_request(webhook_url, message_list)


def main():
    # 環境変数を読み込む
    load_dotenv()
    HOST_NAME = os.getenv("HOST_NAME")
    USER_NAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    # 定数を設定
    DB_NAME = "VCTContractsDB"
    TABLE_NAME = "VCTContractsTable"

    # スプレッドシートのpubhtmlのデータを取得
    data_list_from_spreadsheet = get_spreadsheet_data_list(target_url)
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
    (data_list_update, data_list_added, data_list_removed) = diff_lists_from_data_lists(
        data_list_from_spreadsheet, data_list_from_db
    )
    # DBの更新、追加、削除
    update_data_to_db(connection, TABLE_NAME, data_list_update)
    insert_data_to_db(connection, TABLE_NAME, data_list_added)
    delete_data_from_db(connection, TABLE_NAME, data_list_removed)
    # WEBHOOKを利用してdiffを送信
    post_diff_list(WEBHOOK_URL, data_list_update, data_list_added, data_list_removed)
    # MySQLサーバーとの接続を切断
    connection.close()


if __name__ == "__main__":
    main()
