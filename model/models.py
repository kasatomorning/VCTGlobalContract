from enum import Enum
from utils.utils import normalize_unicode
from dataclasses import dataclass


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


@dataclass
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

    def __post_init__(self):
        self.first_name = normalize_unicode(self.first_name)
        self.family_name = normalize_unicode(self.family_name)
        self.end_date = int(self.end_date) if self.end_date != "" else 0

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


# Discordのリクエストを作成する
# docs:https://birdie0.github.io/discord-webhooks-guide/discord_webhook.html
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

    def __repr__(self) -> str:
        return "DiscordRequestMainContent(color={}, image_url={}, title={})".format(
            self.embeds[0]["color"],
            self.embeds[0]["image"]["url"],
            self.embeds[0]["title"],
        )
