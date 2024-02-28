from __future__ import annotations
import requests
import mysql.connector
from mysql.connector import Error
from bs4 import BeautifulSoup
from enum import Enum
import json
import os
from dotenv import load_dotenv
import time
import copy
import unicodedata
import sys
import re
import requests.packages.urllib3.util.connection as urllib3_cn
import socket


def allowed_gai_family4():
    return socket.AF_INET


urllib3_cn.allowed_gai_family = allowed_gai_family4


target_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmmWiBmMMD43m5VtZq54nKlmj0ZtythsA1qCpegwx-iRptx2HEsG0T3cQlG1r2AIiKxBWnaurJZQ9Q/pubhtml#"

COLUMN_NUM = 11
DB_NAME = "VCTContractsDB"
TABLE_NAME = "VCTContractsTable"

ad_pattern = r"20\d{2}"


class League(Enum):
    PACIFIC = "PACIFIC"
    EMEA = "EMEA"
    AMERICAS = "AMERICAS"
    CN = "CN"


# update:green removed:red added:blue
class Color(Enum):
    UPDATE = 655104
    REMOVED = 16711680
    ADDED = 7935


class SpreadsheetData:
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
        self.first_name = normalize_unicode(first_name)
        self.family_name = normalize_unicode(family_name)
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


def get_spreadsheet_data_list(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tr_element = soup.find_all("tr")
        data_list = []
        for i in tr_element:
            td_elements = i.findAll("td")
            text_list = []
            for j in td_elements:
                text_list.append(j.text)
            # 空行・リーグ名が不正な行・選手名が空の行は無視
            if (
                len(text_list) == 0
                or text_list[0] not in [league.value for league in League]
                or text_list[4] == ""
                or text_list[5] == ""
            ):
                continue
            # End Dateが20xx年の形式でない場合は0にする
            ad_match = re.search(ad_pattern, text_list[6])
            if ad_match:
                text_list[6] = ad_match.group()
            else:
                text_list[6] = ""
            # はじめの11列だけ取得
            data = SpreadsheetData(*text_list[:COLUMN_NUM])
            data_list.append(data)
    except Error as err:
        print("Error: '{}'".format(err))
        exit(1)
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
        print("No data in this list")
        return
    for data in data_list:
        print(data.values())


# リストを2つ受け取り、差分を更新/追加/削除済みの3つのリストに分けて返す
def diff_lists_from_data_lists(
    data_list_new: list[SpreadsheetData], data_list_old: list[SpreadsheetData]
):
    if data_list_new == [] or data_list_old == []:
        print("No data in either list")
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
    print("list_update_old")
    show_data_list(data_list_update_old)
    print("list_update_new")
    show_data_list(data_list_update_new)
    print("list_added")
    show_data_list(data_list_added)
    print("list_removed")
    show_data_list(data_list_removed)
    return (
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    )


def post_request(webhook_url, show_data: list[DiscordRequestMainContent]):
    headers = {"Content-Type": "application/json"}
    # リストが空のときはリクエストを送らない
    if show_data == []:
        print("No data in this list")
        return
    for data in show_data:
        main_content = json.dumps(data.__dict__)
        print(main_content)
        try:
            response = requests.post(
                url=webhook_url, headers=headers, data=main_content, timeout=10
            )
            response.raise_for_status()
            print("Success post request")
            # 大量の更新があった場合でも429が返ってこないようにする
            time.sleep(3)
        except Error as err:
            print("Failed post request: '{}'".format(err))
            exit(1)


def post_diff_list(
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
    post_request(webhook_url, message_list)


def get_picture_from_liquipedia(player_name):
    try:
        request_url = "https://liquipedia.net/valorant/{}".format(player_name)
        print(request_url)
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
        print(e)
        return ""


def normalize_unicode(words: str) -> str:
    unicode_words = ""
    for character in unicodedata.normalize("NFD", words):
        if unicodedata.category(character) != "Mn":
            unicode_words += character
    return unicode_words


def main():
    # 環境変数を読み込む
    load_dotenv()
    HOST_NAME = os.getenv("HOST_NAME")
    USER_NAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

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
    post_diff_list(
        WEBHOOK_URL,
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    )
    # MySQLサーバーとの接続を切断
    connection.close()


def main_simulate():
    """
    本当にDBを更新できるかどうかを試すための関数
    VCTContractsTable2にVCTContractsTableのデータをコピーし更新する
    webhookは利用しない
    """
    # 環境変数を読み込む
    load_dotenv()
    HOST_NAME = os.getenv("HOST_NAME")
    USER_NAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    # 使うテーブル名を設定
    simulate_TABLE_NAME = "VCTContractsTableSimulate"

    # スプレッドシートのpubhtmlのデータを取得
    data_list_from_spreadsheet = get_spreadsheet_data_list(target_url)
    # MySQLサーバーに接続
    connection = connect_to_mysql_server(HOST_NAME, USER_NAME, PASSWORD)
    # DBを作成|存在確認
    create_or_check_database(connection, DB_NAME)
    # DBを選択
    execute_query(connection, "USE {}".format(DB_NAME))
    # テーブルを作成|存在確認
    create_or_check_table(connection, simulate_TABLE_NAME)
    # 既存のデータを削除
    execute_query(
        connection,
        "DELETE FROM {}".format(simulate_TABLE_NAME),
        success_message="Success reset table data",
        error_message="Failed reset table data",
    )
    # 実際のテーブルのデータをコピー
    execute_query(
        connection,
        "INSERT INTO {} SELECT * FROM {};".format(simulate_TABLE_NAME, TABLE_NAME),
        success_message="Success copying table",
        error_message="Failed copying table",
    )
    # テーブルのデータを表示
    data_list_from_db = read_data_from_db(connection, simulate_TABLE_NAME)
    # DBとスプレッドシートのデータを比較し、差分のリストを取得
    (
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    ) = diff_lists_from_data_lists(data_list_from_spreadsheet, data_list_from_db)

    # DBの更新、追加、削除
    update_data_to_db(connection, simulate_TABLE_NAME, data_list_update_new)
    delete_data_from_db(connection, simulate_TABLE_NAME, data_list_removed)
    insert_data_to_db(connection, simulate_TABLE_NAME, data_list_added)
    # WEBHOOKを利用してdiffを送信
    post_diff_list(
        WEBHOOK_URL,
        data_list_update_old,
        data_list_update_new,
        data_list_added,
        data_list_removed,
    )
    # MySQLサーバーとの接続を切断
    connection.close()


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--simulate":
        print("---START simulation mode---")
        main_simulate()
        print("---END simulation mode---")
    else:
        main()
