from helpers.sha1 import calculate_sha1

from typing import Union, IO
from helpers.models.sonolus.misc import SRL

from io import BytesIO
from zipfile import ZipFile
import os
import redis

from helpers.config_loader import get_config

config = get_config()
redis_config = config.get("redis", {})
_redis = redis.Redis(
    host=redis_config.get("host", "127.0.0.1"),
    port=redis_config.get("port", 6379),
    db=redis_config.get("db", 0),
    password=redis_config.get("password", None),
)

REPO_DATA_PREFIX = "repo:data:"
REPO_PATH_PREFIX = "repo:path:"


class Repository:
    def _read_from_zip_chain(self, parts: list[str]) -> bytes:
        current_bytes = None

        for i, part in enumerate(parts):
            if i == 0:
                with open(part, "rb") as f:
                    current_bytes = f.read()
            else:
                with ZipFile(BytesIO(current_bytes)) as zip_file:
                    try:
                        current_bytes = zip_file.read(zip_file.getinfo(part))
                    except KeyError:
                        raise FileNotFoundError(f"{part} not found in zip chain")
        return current_bytes

    def _read_file_bytes(self, file: str) -> bytes:
        if "|" in file:
            return self._read_from_zip_chain(file.split("|"))
        else:
            with open(file, "rb") as f:
                return f.read()

    def add_file(
        self, file: os.PathLike, error_on_file_nonexistent: bool = True
    ) -> str | None:
        if not error_on_file_nonexistent:
            if not os.path.exists(str(file).split("|")[0]):
                return None

        file_path = str(file)
        file_data = self._read_file_bytes(file_path)
        sha1 = calculate_sha1(file_data)

        old_hash = _redis.get(REPO_PATH_PREFIX + file_path)
        if old_hash:
            old_hash = old_hash.decode()
            if old_hash != sha1:
                _redis.delete(REPO_DATA_PREFIX + old_hash)

        _redis.set(REPO_DATA_PREFIX + sha1, file_data)
        _redis.set(REPO_PATH_PREFIX + file_path, sha1)
        return sha1

    def add_bytes(self, data: Union[IO[bytes], bytes]) -> str:
        if isinstance(data, BytesIO):
            data.seek(0)
            raw = data.read()
        elif isinstance(data, bytes):
            raw = data
        else:
            raise ValueError("data must be bytes or BytesIO")

        sha1 = calculate_sha1(raw)
        if not _redis.exists(REPO_DATA_PREFIX + sha1):
            _redis.set(REPO_DATA_PREFIX + sha1, raw)
        return sha1

    def get_file(self, hash: str) -> bytes | None:
        data = _redis.get(REPO_DATA_PREFIX + hash)
        return data

    def get_srl(self, hash: str) -> SRL | None:
        if hash and _redis.exists(REPO_DATA_PREFIX + hash):
            return {"hash": hash, "url": f"/sonolus/repository/{hash}"}
        return None


repo = Repository()
