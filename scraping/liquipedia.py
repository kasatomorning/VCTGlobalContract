import requests
from bs4 import BeautifulSoup

from utils.utils import setup_logger
import time, re, datetime
from typing import Optional

logger = setup_logger(__name__)


class LiquipediaScraper:
    LIQUIPEDIA_URL_FORMAT = "https://liquipedia.net/valorant/{}"
    REX_BIRTH_DATE = re.compile(r"[a-zA-Z]+ [0-9]+, [0-9]+")
    REX_AGE = re.compile(r"age.([0-9]+)")
    REX_LINK_TYPE = re.compile(r"lp-(.+)")

    def __init__(self, player_name):
        # liquipediaからページを取得
        try:
            self.request_url = LiquipediaScraper.LIQUIPEDIA_URL_FORMAT.format(
                player_name
            )
            self.response = requests.get(self.request_url)
            self.response.raise_for_status()
            self.soup = BeautifulSoup(self.response.content, features="html.parser")
        except Exception as e:
            # liquipediaにアクセスできない場合・ユーザーが存在しない場合などは空文字列を返す
            self.soup = None
            logger.debug(e)
        finally:
            time.sleep(1)

        # プロフィール情報を取得して辞書を作成
        try:
            self._profile = {}
            profile_elements = self.soup.find("div", class_="fo-nttax-infobox")
            for content in profile_elements.contents:
                if len(content.contents) >= 2:
                    self._profile[content.contents[0].get_text()] = content.contents[
                        1
                    ].get_text()
        except Exception as e:
            self._profile = None
            logger.debug(e)
        self._links = None
        self._history = None
        self._image_url = None
        self._description = None

    @property
    def scrape_successfully(self) -> bool:
        return self.soup is not None

    def get_links(self) -> list[tuple[str, str]]:
        if self.scrape_successfully and self._links is None:
            self._links = []
            tag_name_flag = False
            player_information = self.soup.find("div", class_="fo-nttax-infobox")
            if player_information is None:
                return self._links
            for info in player_information:
                if tag_name_flag:
                    try:
                        for link_line in info.find_all("a"):
                            try:
                                link_type = self.REX_LINK_TYPE.match(link_line.contents[0]["class"][1]).group(1)
                                self._links.append((link_type, link_line["href"]))
                            except Exception as e:
                                self._links.append(("link", link_line["href"]))
                                logger.debug(e)
                    except Exception as e:
                        logger.debug(e)
                    break
                try:
                    if info.contents[0].contents[0].text == 'Links':
                        tag_name_flag = True
                except IndexError:
                    continue
        return self._links

    def get_history(self) -> Optional[list[tuple[str, str]]]:
        if self.scrape_successfully and self._history is None:
            self._history = []
            tag_name_flag = False
            player_information = self.soup.find("div", class_="fo-nttax-infobox")
            if player_information is None:
                return self._history
            for info in player_information:
                if tag_name_flag:
                    try:
                        for history_line in info.find("tbody"):
                            self._history.append((history_line.contents[0].text, history_line.contents[1].text))
                    except Exception as e:
                        logger.debug(e)
                    break
                try:
                    if info.contents[0].contents[0].text == 'History':
                        tag_name_flag = True
                except IndexError:
                    continue
        return self._history

    def get_image_url(self) -> Optional[str]:
        if self.scrape_successfully and self._image_url is None:
            # パースできなかった場合はNoneが返ってくる
            url = self.soup.find("meta", attrs={"property": "og:image"})["content"]
            if "facebook-image.png" in url:  # 画像がデフォルトの場合
                self._image_url = "https://liquipedia.net/commons/images/a/a4/PlayerImagePlaceholder.png"
            elif url is None:  # リンクが取得できない場合
                self._image_url = "https://liquipedia.net/commons/images/a/a4/PlayerImagePlaceholder.png"
            else:
                self._image_url = url
        return self._image_url

    def get_description(self) -> Optional[str]:
        if self.scrape_successfully and self._description is None:
            self._description = self.soup.find(
                "meta", attrs={"property": "og:description"}
            )["content"]
            if self._description is None:
                self._description = ""
        return self._description

    def get_birth_date(self) -> Optional[datetime.date]:
        if self.scrape_successfully and "Born:" in self._profile:
            try:
                return datetime.datetime.strptime(
                    self.REX_BIRTH_DATE.search(self._profile["Born:"]).group(),
                    "%B %d, %Y",
                ).date()
            except Exception as e:
                logger.debug(e)
        return None

    def get_age(self) -> Optional[int]:
        if self.scrape_successfully and "Born:" in self._profile:
            try:
                print(self._profile["Born:"])
                return int(self.REX_AGE.search(self._profile["Born:"]).group(1))
            except Exception as e:
                logger.debug(e)
        return None

    def get_status(self) -> Optional[str]:
        if self.scrape_successfully and "Status:" in self._profile:
            return self._profile["Status:"]
        else:
            return None

    def get_name(self) -> Optional[str]:
        if self.scrape_successfully and "Name:" in self._profile:
            return self._profile["Name:"]
        else:
            return None

    def get_team(self) -> Optional[str]:
        if self.scrape_successfully and "Team:" in self._profile:
            return self._profile["Team:"]
        else:
            return None
