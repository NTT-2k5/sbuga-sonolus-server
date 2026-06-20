import math

from fastapi import APIRouter, HTTPException, status
from rapidfuzz import fuzz

from core import SonolusRequest
from helpers.data_compilers import compile_engines_list
from helpers.level_builder import fetch_music_data, get_merged_musics, has_music_data
from helpers.models.api.music import Music
from helpers.playlist_builder import build_collaboration_post
from helpers.models.sonolus.response import ServerItemList

router = APIRouter()


@router.get("", response_model=ServerItemList)
async def main(
    request: SonolusRequest,
    page: int = 0,
    keywords: str = "",
    type: str = "",
):
    api = request.app.api
    source = request.app.base_url
    locale = request.state.loc
    localization = request.state.localization
    items_per_page = request.app.get_items_per_page("posts")

    if not has_music_data():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=locale.data_loading
        )

    music_data = await fetch_music_data(api)
    musics = get_merged_musics(
        music_data, request.state.show_spoilers, request.state.localization
    )

    collab_musics = [
        m
        for m in musics
        if m.collaboration
        and m.collaboration_id is not None
        and m.vocals
        and m.difficulties
    ]
    collab_groups: dict[int, list[Music]] = {}
    for m in collab_musics:
        collab_groups.setdefault(m.collaboration_id, []).append(m)

    collab_names: dict[int, str] = {
        cid: songs[0].collaboration for cid, songs in collab_groups.items()
    }

    sorted_ids = sorted(
        collab_groups.keys(),
        key=lambda k: max(m.published_at for m in collab_groups[k]),
        reverse=True,
    )

    if keywords.strip():
        kw = keywords.strip().lower()
        sorted_ids = [
            cid
            for cid in sorted_ids
            if fuzz.partial_ratio(kw, collab_names[cid].lower()) >= 60
        ]

    total = len(sorted_ids)
    page_count = max(1, math.ceil(total / items_per_page))
    start = page * items_per_page
    page_ids = sorted_ids[start : start + items_per_page]

    items = []
    for cid in page_ids:
        songs = collab_groups[cid]
        post = build_collaboration_post(
            collab_name=collab_names[cid],
            collab_id=cid,
            songs=songs,
            source=source,
            spoiler_tag=locale.spoiler,
            songs_count_str=locale.songs_count(len(songs)),
        )
        items.append(post)

    return ServerItemList(pageCount=page_count, items=items)
