# このコードはDBのfirst_name/family_nameフィールドのnormalizeを行うもの
# 現在はクラスのメンバとして保存する際にnormalize_unicodeしているので不要
# おそらく今後使うことはないがいちおう残しておく

import os
from dotenv import load_dotenv
from model.models import normalize_unicode
from main import (
    create_or_check_table,
    read_data_from_db,
    connect_to_mysql_server,
    insert_data_to_db,
    execute_query,
)


# すべてのレコードのfirst_name, family_nameを正規化する
def normalize_records(connection, table_name):
    data_list_from_db = read_data_from_db(connection=connection, table_name=table_name)
    for record in data_list_from_db:
        record.first_name = normalize_unicode(record.first_name)
        record.family_name = normalize_unicode(record.family_name)
    return data_list_from_db


# 現状first_name, family_nameは主キーなので単純に更新できない
# 強引だが、VCTContractsTableのデータをすべて削除して置換する
def main():
    # 環境変数を読み込む
    load_dotenv()
    HOST_NAME = os.getenv("HOST_NAME")
    USER_NAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
    TABLE_NAME = "VCTContractsTable"
    TABLE_NAME_OLD = "VCTContractsTable_old"
    DB_NAME = "VCTContractsDB"
    # MySQLサーバーに接続
    connection = connect_to_mysql_server(HOST_NAME, USER_NAME, PASSWORD)
    # DBを選択
    execute_query(connection, "USE {}".format(DB_NAME))
    # コピー先テーブルの作成
    create_or_check_table(connection, TABLE_NAME_OLD)
    # VCTContractsTableをVCTContractsTable_oldにコピー
    execute_query(
        connection,
        "INSERT INTO {} SELECT * FROM {};".format(TABLE_NAME_OLD, TABLE_NAME),
        success_message="Success copying table",
        error_message="Failed copying table",
    )
    # VCTContractsTableのデータを正規化する
    normalized_records = normalize_records(connection, TABLE_NAME)
    # VCTContractsTableのデータをすべて削除
    execute_query(
        connection,
        "DELETE FROM {}".format(TABLE_NAME),
        success_message="Success reset table data",
        error_message="Failed reset table data",
    )
    # 正規化したデータをVCTContractsTableに挿入
    insert_data_to_db(connection, TABLE_NAME, normalized_records)
    # MySQLサーバーとの接続を切断
    connection.close()


if __name__ == "__main__":
    main()
