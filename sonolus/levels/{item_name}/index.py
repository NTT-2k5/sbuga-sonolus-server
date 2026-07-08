from fastapi import APIRouter, HTTPException, status

from core import SonolusRequest
from helpers.data_compilers import compile_engines_list
import hashlib

from helpers.level_builder import (
    fetch_music_data,
    get_merged_musics,
    parse_level_id,
    parse_custom_level_id,
    build_level_item,
    build_level_description,
    get_chart_info,
    get_other_difficulties,
    get_other_versions,
    get_same_artist_musics,
    has_music_data,
    fetch_custom_chart_metadata,
    get_converted_chart,
)
from helpers.playlist_builder import build_playlist_item
from helpers.models.sonolus.item_section import LevelItemSection, PlaylistItemSection
from helpers.models.sonolus.misc import SRL
from helpers.models.sonolus.response import ServerItemDetails

router = APIRouter()


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
    musics = get_merged_musics(music_data, True, localization)
    engines = await request.app.run_blocking(compile_engines_list, source)

    if not engines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.not_found,
        )

    engine = engines[0]

    parsed = parse_level_id(item_name)
    if parsed:
        return await _handle_official_level(
            request,
            locale,
            source,
            localization,
            music_data,
            musics,
            engine,
            parsed,
            item_name,
        )

    custom_parsed = parse_custom_level_id(item_name)
    if custom_parsed:
        return await _handle_custom_level(
            locale,
            source,
            localization,
            music_data,
            musics,
            engine,
            custom_parsed,
            item_name,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=locale.not_found,
    )


async def _handle_official_level(
    request,
    locale,
    source,
    localization,
    music_data,
    musics,
    engine,
    parsed,
    item_name,
):
    music_id, vocal_id, difficulty_name = parsed

    music = next((m for m in musics if m.id == music_id), None)
    if not music:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.item_not_found("Level", item_name),
        )

    vocal = next((v for v in music.vocals if v.id == vocal_id), None)
    if not vocal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.item_not_found("Level", item_name),
        )

    diff = next(
        (d for d in music.difficulties if d.difficulty == difficulty_name), None
    )
    if not diff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.item_not_found("Level", item_name),
        )

    chart_info = get_chart_info(music.id, difficulty_name)

    level = build_level_item(
        music=music,
        vocal=vocal,
        difficulty_name=difficulty_name,
        play_level=diff.play_level,
        engine=engine,
        source=source,
        localization=localization,
        music_data=music_data,
        levelbg=request.state.levelbg,
        spoiler_tag=locale.spoiler,
    )

    description = build_level_description(
        music=music,
        combo=chart_info["combo"],
        duration=chart_info["duration"],
        music_data=music_data,
        localization=localization,
    )

    sections = []

    other_diff_levels = []
    other_diffs = get_other_difficulties(music, difficulty_name)
    for diff_name, play_level in other_diffs:
        od_level = build_level_item(
            music=music,
            vocal=vocal,
            difficulty_name=diff_name,
            play_level=play_level,
            engine=engine,
            source=source,
            localization=localization,
            music_data=music_data,
            levelbg=request.state.levelbg,
        )
        other_diff_levels.append(od_level)

    other_ver_levels = []
    other_vocals = get_other_versions(music, vocal_id)
    for other_vocal in other_vocals:
        ov_level = build_level_item(
            music=music,
            vocal=other_vocal,
            difficulty_name=difficulty_name,
            play_level=diff.play_level,
            engine=engine,
            source=source,
            localization=localization,
            music_data=music_data,
            levelbg=request.state.levelbg,
        )
        other_ver_levels.append(ov_level)

    if other_diff_levels:
        sections.append(
            LevelItemSection(
                title="#OTHER_DIFFICULTIES",
                icon="level",
                items=other_diff_levels,
            )
        )

    if other_ver_levels:
        sections.append(
            LevelItemSection(
                title="#OTHER_VERSIONS",
                icon="level",
                items=other_ver_levels,
            )
        )

    same_artist = get_same_artist_musics(musics, music)
    if same_artist:
        sa_levels = []
        for sa_music in same_artist:
            if not sa_music.vocals or not sa_music.difficulties:
                continue
            sa_vocal = sa_music.vocals[0]
            sa_diff = sa_music.difficulties[-1]
            sa_level = build_level_item(
                music=sa_music,
                vocal=sa_vocal,
                difficulty_name=sa_diff.difficulty,
                play_level=sa_diff.play_level,
                engine=engine,
                source=source,
                localization=localization,
                music_data=music_data,
                levelbg=request.state.levelbg,
            )
            sa_levels.append(sa_level)
        if sa_levels:
            sections.append(
                LevelItemSection(
                    title="#SAME_AUTHOR",
                    icon="level",
                    items=sa_levels,
                )
            )

    return ServerItemDetails(
        item=level,
        description=description,
        actions=[],
        hasCommunity=False,
        leaderboards=[],
        sections=sections,
    )


async def _handle_custom_level(
    locale,
    source,
    localization,
    music_data,
    musics,
    engine,
    custom_parsed,
    item_name,
):
    from locales.locale import Locale

    loc, _ = Locale.get_messages(localization)
    region, vocal_id, chart_id = custom_parsed

    try:
        metadata = await fetch_custom_chart_metadata(chart_id, region)
    except HTTPException:
        raise

    level1 = metadata.get("userCustomMusicScoreInfoJson") or {}
    inner = level1.get("userCustomMusicScoreInfoJson") or {}
    music_id = inner.get("musicId") or level1.get("musicId")

    if not music_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.not_found,
        )

    music = next((m for m in musics if m.id == music_id), None)
    if not music:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.item_not_found("Level", item_name),
        )

    vocal = next((v for v in music.vocals if v.id == vocal_id), None)
    if not vocal:
        vocal = music.vocals[0] if music.vocals else None
    if not vocal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=locale.item_not_found("Level", item_name),
        )

    try:
        converted_chart, combo_count = await get_converted_chart(chart_id, region)
    except HTTPException:
        raise

    chart_hash = hashlib.sha1(converted_chart).hexdigest()

    difficulty = level1.get("musicDifficultyType", "") or "expert"
    play_level = level1.get("playLevel", 0)
    play_count = level1.get("playCount", 0)
    like_count = level1.get("reviewCount", 0)
    fc_rate = level1.get("fullComboRate")

    level = build_level_item(
        music=music,
        vocal=vocal,
        difficulty_name=difficulty,
        play_level=play_level or 0,
        engine=engine,
        source=source,
        localization=localization,
        music_data=music_data,
        levelbg="v3",
        spoiler_tag=locale.spoiler,
    )
    level.name = item_name
    level.data = SRL(
        hash=chart_hash, url=f"{source}/sonolus/custom_charts/{region}-{chart_id}"
    )

    lines = []
    if difficulty and play_level:
        lines.append(f"{difficulty.title()} {play_level}")
        lines.append("")
    if play_count:
        lines.append(f"{loc.play_count}: {play_count:,}")
    if like_count:
        lines.append(f"{loc.like_count}: {like_count:,}")
    if fc_rate is not None:
        lines.append(f"{loc.fc_rate}: {fc_rate:.1f}%")
    if combo_count:
        lines.append(f"#COMBO:#SEPARATOR_COLON: {combo_count:,}")

    chart_title = inner.get("title")
    if chart_title:
        lines.append("")
        lines.append(chart_title)
    description = "\n".join(lines)

    sections = []

    other_ver_levels = []
    for other_vocal in music.vocals:
        if other_vocal.id == vocal_id:
            continue
        custom_level_id = f"sss-custom-{region}-{other_vocal.id}-{chart_id}"
        ov_level = build_level_item(
            music=music,
            vocal=other_vocal,
            difficulty_name=difficulty,
            play_level=play_level or 0,
            engine=engine,
            source=source,
            localization=localization,
            music_data=music_data,
            levelbg="v3",
            spoiler_tag=locale.spoiler,
        )
        ov_level.name = custom_level_id
        ov_level.data = SRL(
            hash=chart_hash, url=f"{source}/sonolus/custom_charts/{region}-{chart_id}"
        )
        other_ver_levels.append(ov_level)

    if other_ver_levels:
        sections.append(
            LevelItemSection(
                title="#OTHER_VERSIONS",
                icon="level",
                items=other_ver_levels,
            )
        )

    if music.vocals and music.difficulties:
        original_playlist = await build_playlist_item(
            music=music,
            engine=engine,
            source=source,
            localization=localization,
            music_data=music_data,
            spoiler_tag=locale.spoiler,
        )
        sections.append(
            PlaylistItemSection(
                title=locale.original_song,
                icon="playlist",
                items=[original_playlist],
            )
        )

    return ServerItemDetails(
        item=level,
        description=description,
        actions=[],
        hasCommunity=False,
        leaderboards=[],
        sections=sections,
    )
