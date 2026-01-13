"""网易云音乐搜索 API"""

from typing import Any

from .utils.network import get_api
from .exceptions import SearchError, SongNotFoundError


async def search_song(keyword: str) -> dict[str, Any]:
    """搜索歌曲（返回第一个结果）
    
    Args:
        keyword: 搜索关键词（歌曲名 歌手名）
    
    Returns:
        歌曲信息字典，包含 id, name, artists, album 等
    
    Raises:
        SearchError: 搜索请求失败
        SongNotFoundError: 未找到匹配的歌曲
    """
    try:
        api = get_api()
        result = await api.search(keyword, type=1, limit=1)
        
        songs = result.get("result", {}).get("songs", [])
        if not songs:
            raise SongNotFoundError(f"未找到歌曲: {keyword}")
        
        return songs[0]
    except SongNotFoundError:
        raise
    except Exception as e:
        raise SearchError(f"搜索失败: {e}") from e
