from fastapi import APIRouter, HTTPException, status

from core import SonolusRequest
from helpers.data_compilers import compile_engines_list
from helpers.level_builder import fetch_music_data, get_merged_musics, has_music_data
from helpers.models.api.music import Music
from helpers.playlist_builder import build_collaboration_post, sort_collab_groups
from helpers.models.sonolus.item_section import PostItemSection
from helpers.models.sonolus.options import ServerForm, ServerTextOption
from helpers.models.sonolus.response import ServerItemInfo

router = APIRouter()


@router.get("", response_model=ServerItemInfo)
async def main(request: SonolusRequest, type: str = ""):
    locale = request.state.loc
    localization = request.state.localization
    api = request.app.api
    source = request.app.base_url

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

    posts = []
    for cid in sorted(
        collab_groups.keys(),
        key=lambda k: max(m.published_at for m in collab_groups[k]),
        reverse=True,
    ):
        songs = collab_groups[cid]
        cname = songs[0].collaboration
        post = build_collaboration_post(
            collab_name=cname,
            collab_id=cid,
            songs=songs,
            source=source,
            spoiler_tag=locale.spoiler,
            songs_count_str=locale.songs_count(len(songs)),
        )
        posts.append(post)

    sections = []
    if posts:
        sections.append(
            PostItemSection(
                title="#COLLABORATION",
                icon="star",
                items=posts,
            )
        )

    searches = [
        ServerForm(
            type="quick",
            title="#KEYWORDS",
            icon="search",
            requireConfirmation=False,
            options=[
                ServerTextOption(
                    query="keywords",
                    name="#KEYWORDS",
                    required=False,
                    default="",
                    placeholder="#KEYWORDS_PLACEHOLDER",
                    limit=100,
                    shortcuts=[],
                ),
            ],
        ),
    ]

    return ServerItemInfo(
        searches=searches,
        sections=sections,
        banner=None,
    )
