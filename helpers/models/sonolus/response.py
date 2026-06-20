from typing import Annotated
from pydantic import BaseModel, Field

from helpers.models.sonolus.item import ServerItem
from helpers.models.sonolus.item_section import ServerItemSection
from helpers.models.sonolus.misc import SRL, ServerInfoItemButton
from helpers.models.sonolus.options import ServerForm, ServerOption


class ServerItemInfo(BaseModel):
    searches: list[ServerForm] | None = None
    quickSearchValues: str | None = None
    sections: list[Annotated[ServerItemSection, Field(discriminator="itemType")]]
    banner: SRL | None = None


class ServerItemDetails(BaseModel):
    item: ServerItem
    description: str | None = None
    actions: list[ServerForm]
    hasCommunity: bool
    leaderboards: list
    sections: list[Annotated[ServerItemSection, Field(discriminator="itemType")]]


class ServerItemList(BaseModel):
    pageCount: int
    cursor: str | None = None
    items: list[ServerItem]
    searches: list[ServerForm] | None = None
    quickSearchValues: str | None = None


class ServerConfiguration(BaseModel):
    options: list[ServerOption]


class ServerInfo(BaseModel):
    title: str
    description: str | None = None
    buttons: list[ServerInfoItemButton]
    configuration: ServerConfiguration
    banner: SRL | None
