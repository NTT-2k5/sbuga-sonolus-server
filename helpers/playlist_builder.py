from helpers.models.api.music import (
    Music,
    translate_caption,
)
from helpers.models.sonolus.item import PlaylistItem, PostItem, LevelItem
from helpers.models.sonolus.misc import SRL, Tag
from helpers.level_builder import (
    build_level_item,
    get_display_title,
)

_COLLAB_PREFIX = "sss-collab-"


def sort_collab_groups(groups: dict[str, list[Music]]) -> list[str]:
    return sorted(
        groups.keys(),
        key=lambda name: max(m.published_at for m in groups[name]),
        reverse=True,
    )


def make_playlist_id(music_id: int) -> str:
    return f"sss-{music_id}"


def parse_playlist_id(playlist_id: str) -> int | None:
    parts = playlist_id.split("-")
    if len(parts) != 2 or parts[0] != "sss":
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def build_playlist_description(
    music: Music,
    music_data: dict[str, list[Music]] | None = None,
) -> str:
    from helpers.level_builder import _get_all_title_variants

    lines = []
    if music.collaboration:
        lines.append(f"#COLLABORATION:#SEPARATOR_COLON:{music.collaboration}")
        lines.append("")
    if music.artist:
        lines.append(f"#AUTHOR:#SEPARATOR_COLON:{music.artist.name}")
        lines.append("")
    if music.lyricist:
        lines.append(f"#LYRICIST:#SEPARATOR_COLON:{music.lyricist}")
    if music.composer:
        lines.append(f"#COMPOSER:#SEPARATOR_COLON:{music.composer}")
    if music.arranger:
        lines.append(f"#ARRANGER:#SEPARATOR_COLON:{music.arranger}")

    variants = _get_all_title_variants(music, music_data)
    if variants:
        lines.append("")
        lines.append(" ".join(variants))

    return "\n".join(lines)


async def build_playlist_item(
    music: Music,
    engine,
    source: str,
    localization: str = "en",
    music_data: dict[str, list[Music]] | None = None,
    levelbg: str = "v3",
    spoiler_tag: str = "Spoiler",
) -> PlaylistItem:
    import time

    title = music.title
    if music_data:
        title = get_display_title(music.id, music_data, localization)

    tags = []
    if music.published_at > int(time.time() * 1000):
        tags.append(Tag(title=spoiler_tag, icon="show"))

    seen = set()
    for v in music.vocals:
        translated = translate_caption(v.caption, localization)
        if translated not in seen:
            seen.add(translated)
            tags.append(Tag(title=translated))

    sorted_diffs = sorted(music.difficulties, key=lambda d: d.play_level, reverse=True)
    levels: list[LevelItem] = []
    for vocal in music.vocals:
        for diff in sorted_diffs:
            level = build_level_item(
                music=music,
                vocal=vocal,
                difficulty_name=diff.difficulty,
                play_level=diff.play_level,
                engine=engine,
                source=source,
                localization=localization,
                music_data=music_data,
                levelbg=levelbg,
            )
            levels.append(level)

    cover_url = music.jacket_url or ""

    return PlaylistItem(
        name=make_playlist_id(music.id),
        source=source,
        title=title,
        subtitle=f"{len(music.vocals)} version{'s' if len(music.vocals) != 1 else ''}, {len(music.difficulties)} difficult{'ies' if len(music.difficulties) != 1 else 'y'}",
        author=(
            "HATSUNE MIKU: COLORFUL STAGE!"
            if localization == "en"
            else "プロジェクトセカイ カラフルステージ！ feat. 初音ミク"
        ),
        tags=tags,
        levels=levels,
        thumbnail=SRL(url=cover_url),
    )


def build_collaboration_post(
    collab_name: str,
    collab_id: int,
    songs: list[Music],
    source: str,
    spoiler_tag: str = "Spoiler",
    songs_count_str: str = "",
) -> PostItem:
    import time

    latest = max(songs, key=lambda m: m.published_at)
    cover_url = latest.jacket_url or ""

    now_ms = int(time.time() * 1000)
    all_spoiler = all(m.published_at > now_ms for m in songs)
    tags = []
    if all_spoiler:
        tags.append(Tag(title=spoiler_tag, icon="show"))
    tags.append(Tag(title=songs_count_str))

    return PostItem(
        name=f"{_COLLAB_PREFIX}{collab_id}",
        source=source,
        title=collab_name,
        time=latest.published_at,
        author="",
        tags=tags,
        thumbnail=SRL(url=cover_url),
    )
