from model.webhook_structures import DiscordWebhookStructure, Embed
from utils.utils import setup_logger
from scraping.liquipedia import LiquipediaScraper

import json, requests

logger = setup_logger(__name__)


class DiscordMessageSender:
    HEADERS = {"Content-Type": "application/json"}
    TIMEOUT = 10
    SLEEP_INTERVAL = 3

    def __init__(
        self,
        webhook_url: str,
        webhook_structure: DiscordWebhookStructure = DiscordWebhookStructure(),
    ):
        self.webhook_url = webhook_url
        self.webhook_structure = webhook_structure

    def post(self):
        main_content = json.dumps(self.webhook_structure.dict)
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


class DiscordSpreadsheetMessageSender(DiscordMessageSender):
    def __init__(
        self,
        player_name: str,
        webhook_url: str,
        webhook_structure: DiscordWebhookStructure = DiscordWebhookStructure(),
    ):
        super().__init__(webhook_url=webhook_url, webhook_structure=webhook_structure)
        self.liquipedia_scraper = LiquipediaScraper(player_name=player_name)


class DiscordDeletedMessageSender(DiscordSpreadsheetMessageSender):
    TITLE_FORMAT = "{}({} {}, {}) was removed from {}"

    def __init__(
        self,
        player_name: str,
        first_name: str,
        family_name: str,
        role: str,
        team_name: str,
        webhook_url: str,
        webhook_structure: DiscordWebhookStructure = DiscordWebhookStructure(),
    ):
        super().__init__(player_name, webhook_url, webhook_structure)
        self.webhook_structure.embeds = [
            Embed(
                title=self.TITLE_FORMAT.format(
                    player_name, first_name, family_name, role, team_name
                )
            )
        ]


class DiscordAddedMessageSender(DiscordSpreadsheetMessageSender):
    TITLE_FORMAT = "{}({} {}, {}) joined {}"

    def __init__(
        self,
        player_name: str,
        first_name: str,
        family_name: str,
        role: str,
        team_name: str,
        webhook_url: str,
        webhook_structure: DiscordWebhookStructure = DiscordWebhookStructure()
    )
        super().__init__(player_name, webhook_url, webhook_structure)

