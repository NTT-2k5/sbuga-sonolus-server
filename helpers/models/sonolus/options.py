from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field
from helpers.models.sonolus.misc import SIL
from helpers.models.sonolus.validation import *
from helpers.sonolus_typings import Icon, ItemType, Text


class ServerTextOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["text"] = "text"
    default: str = Field(serialization_alias="def")
    placeholder: Text | str
    limit: int
    shortcuts: list[str]

    model_config = ConfigDict(by_alias=True)


class ServerTextAreaOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["textArea"] = "textArea"
    default: str = Field(serialization_alias="def")
    placeholder: Text | str
    limit: int
    shortcuts: list[str]

    model_config = ConfigDict(by_alias=True)


class ServerSliderOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["slider"] = "slider"
    default: int | float = Field(serialization_alias="def")
    min: int | float
    max: int | float
    step: int | float
    unit: Text | str | None = None

    model_config = ConfigDict(by_alias=True)


class ServerToggleOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["toggle"] = "toggle"
    default: bool = Field(serialization_alias="def")

    model_config = ConfigDict(by_alias=True)


class ServerOption_Value(BaseModel):
    name: str
    title: Text | str


class ServerSelectOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["select"] = "select"
    default: str = Field(serialization_alias="def")
    values: list[ServerOption_Value]

    model_config = ConfigDict(by_alias=True)


class ServerMultiOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["multi"] = "multi"
    default: list[bool] = Field(serialization_alias="def")
    values: list[ServerOption_Value]

    model_config = ConfigDict(by_alias=True)


class ServerServerItemOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["serverItem"] = "serverItem"
    itemType: ItemType
    infoType: str | None = None
    default: SIL | None = Field(None, serialization_alias="def")
    allowOtherServers: bool

    model_config = ConfigDict(by_alias=True)


class ServerCollectionItemOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["collectionItem"] = "collectionItem"
    itemType: ItemType


class ServerFileOption(BaseModel):
    query: str
    name: Text | str
    description: str | None = None
    required: bool
    type: Literal["file"] = "file"
    default: str = Field(serialization_alias="def")
    validation: (
        ServerFileOptionValidationFile
        | ServerFileOptionValidationImage
        | ServerFileOptionValidationAudio
        | ServerFileOptionValidationZip
        | ServerFileOptionValidationJson
    ) | None = None

    model_config = ConfigDict(by_alias=True)


ServerOption = (
    ServerTextOption
    | ServerTextAreaOption
    | ServerSliderOption
    | ServerToggleOption
    | ServerSelectOption
    | ServerMultiOption
    | ServerServerItemOption
    | ServerCollectionItemOption
    | ServerFileOption
)


class ServerForm(BaseModel):
    type: str
    title: Text | str
    icon: Icon | str | None = None
    description: str | None = None
    help: str | None = None
    requireConfirmation: bool
    options: list[Annotated[ServerOption, Field(discriminator="type")]]
