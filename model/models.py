from enum import Enum
from utils import normalize_unicode


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

    def __eq__(self, other: "SpreadsheetData"):
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

    def __ne__(self, other: "SpreadsheetData"):
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
