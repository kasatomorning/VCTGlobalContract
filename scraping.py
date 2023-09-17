import requests
import mysql.connector
from mysql.connector import Error
from bs4 import BeautifulSoup
from enum import Enum
import pprint
import os
from dotenv import load_dotenv

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
    is_resident: bool
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
        resident_status: bool,
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
        self.is_resident = resident_status == "Resident"
        self.roster_status = roster_status
        self.team_tag = team_tag
        self.team_contact_info = team_contact_info

    def values(self):
        return [
            self.league,
            self.team_name,
            self.handle_name,
            self.role,
            self.first_name,
            self.family_name,
            self.end_date,
            self.is_resident,
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
    cursor = connection.cursor()
    try:
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET 'utf8'".format(
                db_name
            )
        )
        print("Database created successfully or already exists")
    except Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)


def create_or_check_table(connection, table_name):
    cursor = connection.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS {} (
        league VARCHAR(50),
        team_name VARCHAR(50),
        handle_name VARCHAR(50),
        role VARCHAR(50),
        first_name VARCHAR(50) NOT NULL,
        family_name VARCHAR(50) NOT NULL,
        end_date INT(4) NOT NULL,
        is_resident BOOLEAN,
        roster_status VARCHAR(50),
        team_tag VARCHAR(50),
        team_contact_info VARCHAR(50),
        PRIMARY KEY (first_name, family_name)
    )
    """.format(
        table_name
    )
    try:
        cursor.execute(query)
        print("Table created successfully or already exists")
    except Error as err:
        print("Failed creating table: {}".format(err))
        exit(1)


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as err:
        print("Error: '{}'".format(err))
        exit(1)


def write_data_to_table(connection, table_name, data_list):
    cursor = connection.cursor()
    query = """ INSERT INTO `{}`(
        `league`, `team_name`, `handle_name`,`role`,`first_name`,`family_name`,
        `end_date`,`is_resident`,`roster_status`,`team_tag`,`team_contact_info`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """.format(
        table_name
    )
    # cursor.executemany(query, data_list)
    cursor.executemany(query, [data.values() for data in data_list])
    connection.commit()


def read_data_from_table(connection, table_name):
    # TODO: テーブルのデータを読み込む
    pass


def main():
    # 環境変数を読み込む
    load_dotenv()
    HOST_NAME = os.getenv("HOST_NAME")
    USER_NAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
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
    # テーブルを作成
    create_or_check_table(connection, TABLE_NAME)
    # テーブルのデータを表示
    pprint.pprint([d.values() for d in data_list_from_spreadsheet], width=300)
    # テーブルにデータを書き込み
    write_data_to_table(connection, TABLE_NAME, data_list_from_spreadsheet)
    # MySQLサーバーとの接続を切断
    connection.close()


if __name__ == "__main__":
    main()
