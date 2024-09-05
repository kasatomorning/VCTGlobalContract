import requests
from bs4 import BeautifulSoup
from utils.utils import setup_logger

logger = setup_logger(__name__)


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
