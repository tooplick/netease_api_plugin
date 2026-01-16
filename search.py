"""网易云音乐搜索 API"""

from typing import Any

from .utils.network import get_api, SongInfo
from .exceptions import SearchError, SongNotFoundError


def format_artists(artists: list[dict]) -> str:
    """格式化歌手列表"""
    if not artists:
        return "未知"
    return "/".join(artist.get("name", "未知") for artist in artists)


async def search_song(keyword: str) -> dict[str, Any]:
    """通过 API 搜索歌曲（返回第一个结果）"""
    try:
        api = get_api()
        result = await api.search(keyword, limit=1)
        
        songs = result.get("data", [])
        if not songs:
            raise SongNotFoundError(f"未找到歌曲: {keyword}")
        
        song = songs[0]
        return {
            "id": song.get("id"),
            "name": song.get("name", "未知歌曲"),
            "artists": format_artists(song.get("artists", [])),
            "album": song.get("album", {}).get("name", ""),
            "duration": song.get("duration", ""),
        }
    except SongNotFoundError:
        raise
    except Exception as e:
        raise SearchError(f"搜索失败: {e}") from e


async def get_song_info(song_id: int, level: str = "exhigh") -> SongInfo:
    """获取歌曲完整信息（URL、封面、歌词等）"""
    api = get_api()
    return await api.get_song_info(song_id, level)


async def get_song_url(song_id: int, level: str = "exhigh") -> str:
    """获取歌曲播放链接"""
    api = get_api()
    return await api.get_song_url(song_id, level)


async def get_cover_url(song_id: int, level: str = "exhigh") -> str:
    """获取封面链接"""
    api = get_api()
    return await api.get_cover_url(song_id, level)
