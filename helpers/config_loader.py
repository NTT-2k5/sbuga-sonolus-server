from typing import TypedDict
import yaml

ConfigTypeServer = TypedDict(
    "ConfigTypeServer",
    {
        "port": int,
        "data-worker-port": int,
        "base-url": str,
        "force-https": bool,
        "debug": bool,
    },
)

ItemsPerPage = TypedDict("ItemsPerPage", {"default": int})

ConfigTypeSonolus = TypedDict(
    "ConfigTypeSonolus",
    {
        "required-client-version": str,
        "items-per-page": ItemsPerPage,
        "name": str,
    },
)

ConfigTypeAPI = TypedDict("ConfigTypeAPI", {"url": str, "region-priority": list[str]})

ConfigTypeRedis = TypedDict(
    "ConfigTypeRedis",
    {"host": str, "port": int, "db": int, "password": str | None},
    total=False,
)

ConfigTypeS3 = TypedDict(
    "ConfigTypeS3",
    {
        "base-url": str,
        "endpoint": str,
        "bucket-name": str,
        "access-key-id": str,
        "secret-access-key": str,
        "location": str,
    },
)

ConfigTypePSQL = TypedDict(
    "ConfigTypePSQL",
    {"host": str, "user": str, "database": str, "port": int, "password": str},
)

ConfigType = TypedDict(
    "ConfigType",
    {
        "server": ConfigTypeServer,
        "sonolus": ConfigTypeSonolus,
        "api": ConfigTypeAPI,
        "redis": ConfigTypeRedis,
        "s3": ConfigTypeS3,
        "psql": ConfigTypePSQL,
    },
    total=False,
)

_config: ConfigType | None = None
_config_path: str


def set_config_path(path: str):
    global _config_path, _config
    _config_path = path
    _config = None


def get_config() -> ConfigType:
    global _config
    if _config is None:
        with open(_config_path, "r") as f:
            _config = yaml.load(f, yaml.Loader)
    return _config
