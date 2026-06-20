from pydantic import BaseModel
from helpers.sonolus_typings import Icon, ServerInfoButtonType, Text


class Tag(BaseModel):
    title: Text | str | None = None
    icon: Icon | str | None = None


class SRL(BaseModel):
    hash: str | None = None
    url: str | None = None


class SIL(BaseModel):
    address: str
    name: str


class ServerInfoItemButton(BaseModel):
    type: ServerInfoButtonType
    title: Text | str | None = None
    icon: Icon | str | None = None
    badgeCount: int | None = None
    infoType: str | None = None
    itemName: str | None = None


class ServerMessage(BaseModel):
    message: str
