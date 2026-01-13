"""网易云音乐歌曲 API"""

from typing import Any

from .utils.network import get_api
from .exceptions import SongUrlError


async def get_song_url(song_id: int, level: str = "standard") -> str:
    """获取歌曲播放链接
    
    Args:
        song_id: 歌曲 ID
        level: 音质等级 (standard, higher, exhigh, lossless, hires)
    
    Returns:
        歌曲播放 URL
    
    Raises:
        SongUrlError: 获取链接失败
    """
    try:
        api = get_api()
        result = await api.song_url([song_id], level)
        
        data_list = result.get("data", [])
        if not data_list:
            raise SongUrlError("未获取到歌曲链接")
        
        url = data_list[0].get("url")
        if not url:
            raise SongUrlError("歌曲链接为空，可能需要 VIP 或版权受限")
        
        return url
    except SongUrlError:
        raise
    except Exception as e:
        raise SongUrlError(f"获取歌曲链接失败: {e}") from e


async def get_song_detail(song_id: int) -> dict[str, Any]:
    """获取歌曲详情
    
    Args:
        song_id: 歌曲 ID
    
    Returns:
        歌曲详情字典
    """
    api = get_api()
    result = await api.song_detail([song_id])
    
    songs = result.get("songs", [])
    if not songs:
        return {}
    
    return songs[0]
