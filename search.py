"""网易云音乐搜索 API"""

from typing import Any

from .utils.network import get_api
from .exceptions import SearchError, SongNotFoundError


def format_artists(artists: list[dict]) -> str:
    """格式化歌手列表"""
    if not artists:
        return "未知"
    return "/".join(artist.get("name", "未知") for artist in artists)


async def search_song(keyword: str) -> dict[str, Any]:
    """通过网易云 API 搜索歌曲（返回第一个结果）"""
    try:
        api = get_api()
        result = await api.search(keyword, type=1, limit=1)
        
        songs = result.get("result", {}).get("songs", [])
        if not songs:
            raise SongNotFoundError(f"未找到歌曲: {keyword}")
        
        song = songs[0]
        return {
            "id": song.get("id"),
            "name": song.get("name", "未知歌曲"),
            "artists": format_artists(song.get("ar", [])),
            "album": song.get("al", {}).get("name", ""),
            "duration": song.get("dt", 0),
        }
    except SongNotFoundError:
        raise
    except Exception as e:
        raise SearchError(f"搜索失败: {e}") from e


async def get_song_url(song_id: int) -> str:
    """通过 NodeJS API 获取完整歌曲播放链接"""
    api = get_api()
    return await api.get_song_url(song_id)


async def get_cover_url(song_id: int) -> str:
    """通过 Meting API 获取封面链接"""
    api = get_api()
    return await api.get_cover_url(song_id)
