from enum import Enum, auto
from model.models import SpreadsheetData
from model.webhook_structures import DiscordWebhookStructure, Embed, Field, Image, Thumbnail
from utils.utils import setup_logger
from scraping.liquipedia import LiquipediaScraper

import json, requests, time

logger = setup_logger(__name__)


class DiscordMessageSender:
    HEADERS = {"Content-Type": "application/json"}
    TIMEOUT = 10
    SLEEP_INTERVAL = 3

    def __init__(
        self,
        webhook_url: str,
        webhook_structure: DiscordWebhookStructure = None,
    ):
        self.webhook_url = webhook_url
        self.webhook_structure = webhook_structure
        if webhook_structure is None:
            self.webhook_structure = DiscordWebhookStructure()

    def post(self):
        main_content = json.dumps(self.webhook_structure.dict())
        logger.debug(main_content)
        try:
            response = requests.post(
                url=self.webhook_url,
                headers=self.HEADERS,
                data=main_content,
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            logger.debug("Success post request")
        except Exception as err:
            logger.warning("Failed post request: '{}'".format(err))
            raise
        finally:
            time.sleep(self.SLEEP_INTERVAL)


class DiscordSpreadsheetMessageSender(DiscordMessageSender):
    def __init__(
        self,
        player_name: str,
        webhook_url: str,
        webhook_structure: DiscordWebhookStructure = None,
    ):
        super().__init__(webhook_url=webhook_url, webhook_structure=webhook_structure)
        self.liquipedia_scraper = LiquipediaScraper(player_name=player_name)
        if self.liquipedia_scraper.scrape_successfully():
            self.webhook_structure.embeds = [
                Embed(
                    description=self.liquipedia_scraper.get_description(),
                    fields=[
                        Field(name="Age", value=self.liquipedia_scraper.get_age()),
                        Field(
                            name="Links",
                            value=", ".join(
                                map(
                                    lambda x: "[{}]({})".format(x[0], x[1]),
                                    self.liquipedia_scraper.get_links(),
                                )
                            ),
                        ),
                        Field(
                            name="History",
                            value="\n".join(
                                map(
                                    lambda x: "{}: {}".format(x[0], x[1]),
                                    self.liquipedia_scraper.get_history(),
                                )
                            ),
                        ),
                    ],
                    image=Image(url=self.liquipedia_scraper.get_image_url()),
                )
            ]


class DiscordTeamUpdatedMessageSender(DiscordSpreadsheetMessageSender):
    TEAM_TITLE_FORMAT = "{}({} {}, {}, ex-{}) joined {}"
    COLOR = 0x118822

    def __init__(self, old_data: SpreadsheetData, new_data: SpreadsheetData, webhook_url: str):
        super().__init__(new_data.handle_name, webhook_url)
        self.webhook_structure.embeds[0].color = self.COLOR
        self.webhook_structure.embeds[0].title = self.TEAM_TITLE_FORMAT.format(
            new_data.handle_name,
            new_data.first_name,
            new_data.family_name,
            new_data.role,
            old_data.team_name,
            new_data.team_name,
        )


class DiscordEndDateUpdatedMessageSender(DiscordSpreadsheetMessageSender):
    END_DATE_TITLE_FORMAT = "The end date of {}({} {}, {} in {}) was changed from {} to {}"
    COLOR = 0x118822

    def __init__(self, old_data: SpreadsheetData, new_data: SpreadsheetData, webhook_url: str):
        super().__init__(new_data.handle_name, webhook_url)
        self.webhook_structure.embeds[0].color = self.COLOR
        self.webhook_structure.embeds[0].title = self.END_DATE_TITLE_FORMAT.format(
            new_data.handle_name,
            new_data.first_name,
            new_data.family_name,
            new_data.role,
            new_data.team_name,
            old_data.end_date,
            new_data.end_date,
        )

class DiscordRosterUpdatedMessageSender(DiscordSpreadsheetMessageSender):
    ROSTER_TITLE_FORMAT = "{}({} {}, {} in {}) is {} now"
    COLOR = 0x118822

    def __init__(self, old_data: SpreadsheetData, new_data: SpreadsheetData, webhook_url: str):
        super().__init__(new_data.handle_name, webhook_url)
        self.webhook_structure.embeds[0].color = self.COLOR
        self.webhook_structure.embeds[0].title = self.ROSTER_TITLE_FORMAT.format(
            new_data.handle_name,
            new_data.first_name,
            new_data.family_name,
            new_data.role,
            new_data.team_name,
            new_data.roster_status,
        )

class DiscordRoleUpdatedMessageSender(DiscordSpreadsheetMessageSender):
    ROLE_TITLE_FORMAT = "{}({} {} in {}) changed role from {} to {}"
    COLOR = 0x118822

    def __init__(self, old_data: SpreadsheetData, new_data: SpreadsheetData, webhook_url: str):
        super().__init__(new_data.handle_name, webhook_url)
        self.webhook_structure.embeds[0].color = self.COLOR
        self.webhook_structure.embeds[0].title = self.ROLE_TITLE_FORMAT.format(
            new_data.handle_name,
            new_data.first_name,
            new_data.family_name,
            new_data.team_name,
            old_data.role,
            new_data.role,
        )


class DiscordDeletedMessageSender(DiscordSpreadsheetMessageSender):
    TITLE_FORMAT = "{}({} {}, {}) was removed from {}"
    COLOR = 0xdd3322

    def __init__(
        self,
        data: SpreadsheetData,
        webhook_url: str,
    ):
        super().__init__(data.handle_name, webhook_url)
        self.webhook_structure.embeds[0].color = self.COLOR
        self.webhook_structure.embeds[0].title = self.TITLE_FORMAT.format(
            data.handle_name,
            data.first_name,
            data.family_name,
            data.role,
            data.team_name,
        )


class DiscordAddedMessageSender(DiscordSpreadsheetMessageSender):
    TITLE_FORMAT = "{}({} {}, {}) joined {}"
    COLOR = 0x2266ee

    def __init__(
        self,
        data: SpreadsheetData,
        webhook_url: str,
    ):
        super().__init__(data.handle_name, webhook_url)
        self.webhook_structure.embeds[0].color = self.COLOR
        self.webhook_structure.embeds[0].title = self.TITLE_FORMAT.format(
            data.handle_name,
            data.first_name,
            data.family_name,
            data.role,
            data.team_name,
        )

