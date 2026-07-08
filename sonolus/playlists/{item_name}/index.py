from fastapi import APIRouter, HTTPException, status

import aiohttp

from core import SonolusRequest
from helpers.data_compilers import compile_engines_list
from helpers.level_builder import (
    fetch_music_data,
    get_merged_musics,
    has_music_data,
    get_converted_chart,
    fetch_custom_chart_metadata,
    build_level_item,
)
from helpers.playlist_builder import (
    parse_playlist_id,
    parse_playlist_custom_level_id,
    build_playlist_item,
    build_playlist_description,
)
from helpers.models.sonolus.response import ServerItemDetails
from helpers.models.sonolus.item import PlaylistItem
from helpers.models.sonolus.misc import SRL, Tag

router = APIRouter()


async def build_custom_playlist_item(
    music,
    engine,
    source,
    localization,
    music_data,
    chart_id,
    region,
    metadata,
    converted_chart,
    combo_count,
    spoiler_tag,
):
    title = music.title

    tags = []

    level1 = metadata
    difficulty = level1.get("musicDifficultyType", "")
    play_level = level1.get("playLevel", 0)
    review_count = metadata.get("reviewCount", 0)
    play_count = metadata.get("playCount", 0)

    difficulty_tag = (
        f"{difficulty.title()} {play_level}" if difficulty and play_level else ""
    )
    if difficulty_tag:
        tags.append(Tag(title=difficulty_tag))

    if review_count:
        tags.append(Tag(title=f"likes: {review_count}"))
    if play_count:
        tags.append(Tag(title=f"plays: {play_count}"))
    if combo_count:
        tags.append(Tag(title=f"fc: {combo_count}"))

    levels = []
    for vocal in music.vocals:
        custom_level_id = f"sss-custom-{region}-{vocal.id}-{chart_id}"
        level = build_level_item(
            music=music,
            vocal=vocal,
            difficulty_name=difficulty or "expert",
            play_level=play_level or 0,
            engine=engine,
            source=source,
            localization=localization,
            music_data=music_data,
            levelbg="v3",
            spoiler_tag=spoiler_tag,
        )
        level.name = custom_level_id
        level.data = SRL(url=f"{source}/levels/{custom_level_id}/index.py")
        levels.append(level)

    cover_url = music.jacket_url or ""

    return PlaylistItem(
        name=f"sss-custom-{region}-{chart_id}",
        source=source,
        title=title,
        subtitle=difficulty_tag or "",
        author=(
            "HATSUNE MIKU: COLORFUL STAGE!"
            if localization == "en"
            else "プロジェクトセカイ カラフルステージ！ feat. 初音ミク"
        ),
        tags=tags,
        levels=levels,
        thumbnail=SRL(url=cover_url),
    )


def build_custom_playlist_description(
    music, metadata, combo_count, music_data, localization
):
    lines = []

    level1 = metadata
    difficulty = level1.get("musicDifficultyType", "")
    play_level = level1.get("playLevel", 0)

    if difficulty and play_level:
        lines.append(f"{difficulty.title()} {play_level}")
        lines.append("")

    review_count = metadata.get("reviewCount", 0)
    play_count = metadata.get("playCount", 0)

    if review_count:
        lines.append(f"#REVIEWS:#SEPARATOR_COLON:{review_count}")
    if play_count:
        lines.append(f"#PLAYS:#SEPARATOR_COLON:{play_count}")
    if combo_count:
        lines.append(f"#FC:#SEPARATOR_COLON:{combo_count}")

    inner = metadata.get("userCustomMusicScoreInfoJson") or {}
    inner_inner = inner.get("userCustomMusicScoreInfoJson") or {}
    chart_title = inner_inner.get("title")
    if chart_title:
        lines.append("")
        lines.append(chart_title)

    if music:
        variants = []
        for source_list in (music_data or {}).values():
            for m in source_list:
                if m.id != music.id:
                    continue
                for v in [m.title, m.pronunciation, *m.title_variants]:
                    if v and v not in variants:
                        variants.append(v)
        for v in [music.title, music.pronunciation, *music.title_variants]:
            if v and v not in variants:
                variants.append(v)
        if variants:
            lines.append("")
            lines.append(" ".join(variants))

    return "\n".join(lines)


@router.get("", response_model=ServerItemDetails)
async def main(request: SonolusRequest, item_name: str):
    locale = request.state.loc
    api = request.app.api
    source = request.app.base_url
    localization = request.state.localization

    if not has_music_data():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=locale.data_loading
        )

    music_data = await fetch_music_data(api)
    musics = get_merged_musics(music_data, True, request.state.localization)
    engines = await request.app.run_blocking(compile_engines_list, source, localization)

    if not engines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.not_found,
        )

    engine = engines[0]

    music_id = parse_playlist_id(item_name)
    if music_id is not None:
        music = next((m for m in musics if m.id == music_id), None)
        if not music or not music.vocals or not music.difficulties:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=locale.item_not_found("Playlist", item_name),
            )

        playlist = await build_playlist_item(
            music=music,
            engine=engine,
            source=source,
            localization=localization,
            music_data=music_data,
            spoiler_tag=locale.spoiler,
        )

        description = build_playlist_description(
            music, music_data=music_data, localization=localization
        )

        return ServerItemDetails(
            item=playlist,
            description=description,
            actions=[],
            hasCommunity=False,
            leaderboards=[],
            sections=[],
        )

    parsed = parse_playlist_custom_level_id(item_name)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.not_found,
        )

    region, custom_chart_id = parsed

    try:
        metadata = await fetch_custom_chart_metadata(custom_chart_id, region)
    except HTTPException:
        raise

    inner = metadata.get("userCustomMusicScoreInfoJson") or {}
    inner_inner = inner.get("userCustomMusicScoreInfoJson") or {}
    music_id_from_chart = inner_inner.get("musicId")

    if not music_id_from_chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.not_found,
        )

    music = next((m for m in musics if m.id == music_id_from_chart), None)
    if not music or not music.vocals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.item_not_found("Playlist", item_name),
        )

    try:
        converted_chart, combo_count = await get_converted_chart(
            custom_chart_id, region
        )
    except HTTPException:
        raise

    playlist = await build_custom_playlist_item(
        music=music,
        engine=engine,
        source=source,
        localization=localization,
        music_data=music_data,
        chart_id=custom_chart_id,
        region=region,
        metadata=metadata,
        converted_chart=converted_chart,
        combo_count=combo_count,
        spoiler_tag=locale.spoiler,
    )

    description = build_custom_playlist_description(
        music, metadata, combo_count, music_data, localization
    )

    return ServerItemDetails(
        item=playlist,
        description=description,
        actions=[],
        hasCommunity=False,
        leaderboards=[],
        sections=[],
    )
