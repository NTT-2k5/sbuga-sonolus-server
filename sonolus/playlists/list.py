import math

from fastapi import APIRouter

from core import SonolusRequest
from helpers.data_compilers import compile_engines_list
from helpers.level_builder import (
    fetch_music_data,
    get_merged_musics,
    get_display_title,
)
from helpers.playlist_builder import build_playlist_item
from helpers.models.sonolus.response import ServerItemList

router = APIRouter()


@router.get("", response_model=ServerItemList)
async def main(
    request: SonolusRequest,
    page: int = 0,
    keywords: str = "",
):
    api = request.app.api
    source = request.app.base_url
    localization = request.state.localization
    items_per_page = request.app.get_items_per_page("playlists")

    music_data = await fetch_music_data(api)
    musics = get_merged_musics(
        music_data, request.state.show_spoilers, request.state.localization
    )
    engines = await request.app.run_blocking(compile_engines_list, source, localization)

    if not engines:
        return ServerItemList(pageCount=0, items=[])

    engine = engines[0]

    keywords_lower = keywords.lower().strip()
    if keywords_lower:
        filtered = []
        for music in musics:
            title = get_display_title(music.id, music_data, localization).lower()
            artist_name = music.artist.name.lower() if music.artist else ""
            if (
                keywords_lower in title
                or keywords_lower in artist_name
                or keywords_lower in music.title.lower()
                or (
                    music.pronunciation
                    and keywords_lower in music.pronunciation.lower()
                )
            ):
                filtered.append(music)
        musics = filtered

    musics = [m for m in musics if m.vocals and m.difficulties]
    musics.sort(key=lambda m: m.published_at, reverse=True)

    total = len(musics)
    page_count = max(1, math.ceil(total / items_per_page))

    start = page * items_per_page
    page_musics = musics[start : start + items_per_page]

    items = []
    for music in page_musics:
        playlist = await build_playlist_item(
            music=music,
            engine=engine,
            api=api,
            source=source,
            localization=localization,
            music_data=music_data,
        )
        items.append(playlist)

    return ServerItemList(pageCount=page_count, items=items)
