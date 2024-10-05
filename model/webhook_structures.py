from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class WebhookStructure:
    def dict(self):
        return asdict(
            self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}
        )


@dataclass
class Author(WebhookStructure):
    name: str
    url: Optional[str] = None
    icon_url: Optional[str] = None


@dataclass
class Field(WebhookStructure):
    name: str
    value: str
    inline: Optional[bool] = None

@dataclass
class Image(WebhookStructure):
    url: str
    proxy_url: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None

@dataclass
class Thumbnail(WebhookStructure):
    url: str
    proxy_url: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None

@dataclass
class Embed(WebhookStructure):
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[str] = None
    color: Optional[int] = None
    # footer
    image: Optional[Image] = None
    thumbnail: Optional[Thumbnail] = None
    # video
    # provider
    author: Optional[Author] = None
    fields: list[Field] = None


@dataclass
class DiscordWebhookStructure(WebhookStructure):
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    content: Optional[str] = None
    embeds: Optional[list[Embed]] = None
