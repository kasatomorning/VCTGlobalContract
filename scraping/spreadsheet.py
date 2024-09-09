import requests
from bs4 import BeautifulSoup
import re
from model.models import SpreadsheetData, League
from utils.utils import setup_logger
import conf.global_values as g

logger = setup_logger(__name__)


def get_spreadsheet_data_list(url: str) -> list[SpreadsheetData]:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tr_element = soup.find_all("tr")
        data_list = []
        for i in tr_element:
            td_elements = i.findAll("td")
            text_list = []
            for ele in td_elements:
                text_list.append(ele.text.rstrip())
            if is_validate_text_list(text_list):
                data_list.append(format_text_list(text_list))
    # memo：https://3.python-requests.org/user/quickstart/#errors-and-exceptions
    # 必要に応じて今後追加する
    except Exception as err:
        logger.error("Error: '{}'".format(err))
        exit(1)
    return data_list


# listを引数に受け取る
def is_validate_text_list(text_list: list[str]):
    # 空行・リーグ名が不正な行・選手名が空の行は無視
    if (
        len(text_list) == 0
        or text_list[0] not in [league.value for league in League]
        or text_list[4] == ""
        or text_list[5] == ""
    ):
        return False
    return True


def format_text_list(text_list: list[str]) -> SpreadsheetData:
    ad_pattern = r"20\d{2}"
    # End Dateが20xx年の形式でない場合は0にする
    ad_match = re.search(ad_pattern, text_list[6])
    if ad_match:
        text_list[6] = ad_match.group()
    else:
        text_list[6] = "0"
    # はじめの11列だけ取得
    data = SpreadsheetData(*text_list[: g.COLUMN_NUM])
    return data
