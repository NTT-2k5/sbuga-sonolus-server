from typing import Literal
from pydantic import BaseModel


class ServerFileOptionValidationFile(BaseModel):
    type: Literal["file", "engineRom"]
    minSize: int | float | None = None
    maxSize: int | float | None = None


class ServerFileOptionValidationImage(BaseModel):
    type: Literal[
        "image",
        "serverBanner",
        "postThumbnail",
        "playlistThumbnail",
        "levelCover",
        "skinThumbnail",
        "skinTexture",
        "backgroundThumbnail",
        "backgroundImage",
        "effectThumbnail",
        "particleThumbnail",
        "particleTexture",
        "engineThumbnail",
        "roomCover",
    ]
    minSize: int | float | None = None
    maxSize: int | float | None = None
    minWidth: int | float | None = None
    maxWidth: int | float | None = None
    minHeight: int | float | None = None
    maxHeight: int | float | None = None


class ServerFileOptionValidationAudio(BaseModel):
    type: Literal["audio", "levelBgm", "levelPreview", "roomBgm", "roomPreview"]
    minSize: int | float | None = None
    maxSize: int | float | None = None
    minLength: int | float | None = None
    maxLength: int | float | None = None


class ServerFileOptionValidationZip(BaseModel):
    type: Literal["zip", "effectAudio"]
    minSize: int | float | None = None
    maxSize: int | float | None = None


class ServerFileOptionValidationJson(BaseModel):
    type: Literal[
        "levelData",
        "skinData",
        "backgroundData",
        "backgroundConfiguration",
        "effectData",
        "particleData",
        "enginePlayData",
        "engineWatchData",
        "enginePreviewData",
        "engineTutorialData",
        "engineConfiguration",
        "replayData",
        "replayConfiguration",
    ]
    minSize: int | float | None = None
    maxSize: int | float | None = None
