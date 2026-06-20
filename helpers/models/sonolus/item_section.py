from typing import Literal, TypeAlias
from pydantic import BaseModel

from helpers.models.sonolus.item import *
from helpers.models.sonolus.options import ServerForm
from helpers.sonolus_typings import Icon, ItemType, Text


class ServerItemSectionTyped(BaseModel):
    title: str | Text
    icon: Icon | str | None = None
    description: str | None = None
    help: str | None = None
    itemType: ItemType
    search: ServerForm | None = None
    searchValues: str | None = None


class PostItemSection(ServerItemSectionTyped):
    itemType: Literal["post"] = "post"
    items: list[PostItem]


class PlaylistItemSection(ServerItemSectionTyped):
    itemType: Literal["playlist"] = "playlist"
    items: list[PlaylistItem]


class LevelItemSection(ServerItemSectionTyped):
    itemType: Literal["level"] = "level"
    items: list[LevelItem]


class SkinItemSection(ServerItemSectionTyped):
    itemType: Literal["skin"] = "skin"
    items: list[SkinItem]


class BackgroundItemSection(ServerItemSectionTyped):
    itemType: Literal["background"] = "background"
    items: list[BackgroundItem]


class EffectItemSection(ServerItemSectionTyped):
    itemType: Literal["effect"] = "effect"
    items: list[EffectItem]


class ParticleItemSection(ServerItemSectionTyped):
    itemType: Literal["particle"] = "particle"
    items: list[ParticleItem]


class EngineItemSection(ServerItemSectionTyped):
    itemType: Literal["engine"] = "engine"
    items: list[EngineItem]


class UserItemSection(ServerItemSectionTyped):
    itemType: Literal["user"] = "user"
    items: list[UserItem]


ServerItemSection: TypeAlias = (
    PostItemSection
    | PlaylistItemSection
    | LevelItemSection
    | SkinItemSection
    | BackgroundItemSection
    | EffectItemSection
    | ParticleItemSection
    | EngineItemSection
    | UserItemSection
)
