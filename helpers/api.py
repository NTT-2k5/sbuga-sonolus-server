import time
import aiohttp

from helpers.models.api.music import Music


class SbugaAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

        self._music_cache: dict[str, list[Music]] = {}
        self._music_cache_time: dict[str, float] = {}
        self._cache_ttl = 300

        self._last_data_version: dict[str, str | None] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_version(self, region: str = "en") -> dict:
        session = await self._get_session()
        url = f"{self.base_url}/api/pjsk_data/version?region={region}"
        async with session.get(url) as resp:
            if resp.status != 200:
                return {}
            return await resp.json()

    async def check_and_invalidate(self, region: str = "en") -> bool:
        version_data = await self.get_version(region)
        current = version_data.get("data_version")
        if not current:
            return False

        old = self._last_data_version.get(region)
        if old and old != current:
            self._last_data_version[region] = current
            return True

        self._last_data_version[region] = current
        return False

    async def get_musics(self, region: str = "en", force: bool = False) -> list[Music]:
        now = time.time()
        cache_key = f"musics_{region}"
        if (
            cache_key in self._music_cache
            and now - self._music_cache_time.get(cache_key, 0) < self._cache_ttl
        ) and not force:
            return self._music_cache[cache_key]

        session = await self._get_session()
        url = f"{self.base_url}/api/pjsk_data/musics?region={region}&ignore_leak=true"
        async with session.get(url) as resp:
            if resp.status != 200:
                if cache_key in self._music_cache:
                    return self._music_cache[cache_key]
                resp.raise_for_status()
            data = await resp.json()

        musics_raw = data if isinstance(data, list) else data.get("musics", [])
        musics = [Music.model_validate(m) for m in musics_raw]
        self._music_cache[cache_key] = musics
        self._music_cache_time[cache_key] = now
        return musics

    async def get_asset_bytes(
        self, asset_path: str, region: str = "auto"
    ) -> bytes | None:
        session = await self._get_session()
        url = f"{self.base_url}/api/pjsk_data/assets/{asset_path}?region={region}"
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.read()

    async def get_chart_file(
        self, music_id: int, difficulty: str, region: str = "auto"
    ) -> bytes | None:
        padded_id = f"{music_id:04d}"
        path = f"music/music_score/{padded_id}_01/{difficulty}.txt"
        return await self.get_asset_bytes(path, region)

    def invalidate_music_cache(self):
        self._music_cache.clear()
        self._music_cache_time.clear()
