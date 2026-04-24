"""网易云音乐搜索 API"""

from typing import Any
from urllib.parse import urlparse, parse_qs

from .utils.network import get_api
from .exceptions import SearchError, SongNotFoundError


def format_artists(artists: list[dict]) -> str:
    """格式化歌手列表"""
    if not artists:
        return "未知"
    return "/".join(artist.get("name", "未知") for artist in artists)


async def search_song(keyword: str) -> dict[str, Any]:
    """通过 Meting API 搜索歌曲（返回第一个结果）"""
    try:
        api = get_api()
        results = await api.search(keyword, limit=1)

        if not results:
            raise SongNotFoundError(f"未找到歌曲: {keyword}")

        song = results[0]
        artist = song.get("artist", [])
        if isinstance(artist, list):
            artist_str = "/".join(artist) if artist else "未知"
        else:
            artist_str = str(artist) if artist else "未知"

        song_id = None
        url_field = song.get("url", "")
        if url_field:
            id_values = parse_qs(urlparse(url_field).query).get("id")
            if id_values:
                try:
                    song_id = int(id_values[0])
                except (ValueError, IndexError):
                    pass

        pic_id = None
        pic_field = song.get("pic", "")
        if pic_field:
            id_values = parse_qs(urlparse(pic_field).query).get("id")
            if id_values:
                try:
                    pic_id = id_values[0]
                except (ValueError, IndexError):
                    pass

        return {
            "id": song_id,
            "name": song.get("name", "未知歌曲"),
            "artists": artist_str,
            "album": song.get("album", ""),
            "duration": 0,
            "pic_id": pic_id,
        }
    except SongNotFoundError:
        raise
    except Exception as e:
        raise SearchError(f"搜索失败: {e}") from e


async def get_song_url(song_id: int, br: str = "320") -> str:
    """获取歌曲播放链接"""
    api = get_api()
    return await api.get_song_url(song_id, br)


async def get_cover_url(pic_id: int, cover: str = "500") -> str:
    """获取封面链接"""
    from .utils.network import get_api
    api = get_api()
    return await api.get_cover_url(pic_id, cover)
