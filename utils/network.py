"""网易云音乐 API 网络请求封装"""

from typing import Any, Optional
from dataclasses import dataclass

from ..exceptions import NetEaseAPIError


# 新 API 基础地址
API_BASE_URL = "https://api.kxzjoker.cn"


@dataclass
class SongInfo:
    """歌曲完整信息"""
    id: int
    name: str
    artist: str
    album: str
    url: str
    cover: str
    level: str
    size: str
    lyric: str = ""


class NetEaseAPI:
    """网易云音乐 API 客户端"""
    
    DEFAULT_TIMEOUT = 15.0
    
    def __init__(self, base_url: str = API_BASE_URL):
        """初始化 API 客户端
        
        Args:
            base_url: API 服务基础地址
        """
        self.base_url = base_url.rstrip("/")
        self._client = None
    
    @property
    def client(self):
        """获取 HTTP 客户端实例（延迟导入 httpx）"""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                timeout=self.DEFAULT_TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
                }
            )
        return self._client
    
    async def close(self):
        """关闭客户端连接"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def search(
        self, 
        keywords: str, 
        limit: int = 1,
    ) -> dict:
        """通过 API 搜索歌曲
        
        Args:
            keywords: 搜索关键词
            limit: 返回数量 (1-100)
        
        Returns:
            搜索结果字典
        """
        import httpx
        try:
            url = f"{self.base_url}/api/163_search"
            params = {
                "name": keywords,
                "limit": limit
            }
            resp = await self.client.get(url, params=params)
            resp.encoding = "utf-8"
            resp.raise_for_status()
            data = resp.json()
            
            code = data.get("code", 200)
            if code != 200:
                raise NetEaseAPIError(f"API 返回错误: code={code}", data)
            
            return data
        except httpx.HTTPError as e:
            raise NetEaseAPIError(f"HTTP 请求失败: {e}") from e

    async def get_song_info(
        self, 
        song_id: int,
        level: str = "exhigh"
    ) -> SongInfo:
        """获取歌曲完整信息（URL、封面、歌词等）
        
        Args:
            song_id: 歌曲 ID
            level: 音质等级 (standard/exhigh/lossless/hires/jymaster)
        
        Returns:
            SongInfo 对象
        """
        import httpx
        try:
            url = f"{self.base_url}/api/163_music"
            params = {
                "ids": song_id,
                "level": level,
                "type": "json"
            }
            resp = await self.client.get(url, params=params)
            resp.encoding = "utf-8"
            resp.raise_for_status()
            data = resp.json()
            
            status = data.get("status", 200)
            if status != 200:
                error_msg = data.get("msg", data.get("error", "未知错误"))
                raise NetEaseAPIError(f"获取歌曲信息失败: {error_msg}", data)
            
            song_url = data.get("url")
            if not song_url:
                raise NetEaseAPIError("未获取到歌曲播放链接")
            
            return SongInfo(
                id=song_id,
                name=data.get("name", "未知歌曲"),
                artist=data.get("ar_name", "未知"),
                album=data.get("al_name", ""),
                url=song_url,
                cover=data.get("pic", ""),
                level=data.get("level", ""),
                size=data.get("size", ""),
                lyric=data.get("lyric", "")
            )
        except NetEaseAPIError:
            raise
        except httpx.HTTPError as e:
            raise NetEaseAPIError(f"HTTP 请求失败: {e}") from e
        except Exception as e:
            raise NetEaseAPIError(f"获取歌曲信息失败: {e}") from e

    async def get_song_url(self, song_id: int, level: str = "exhigh") -> str:
        """获取歌曲播放链接
        
        Args:
            song_id: 歌曲 ID
            level: 音质等级
        
        Returns:
            歌曲播放 URL
        """
        info = await self.get_song_info(song_id, level)
        return info.url

    async def get_cover_url(self, song_id: int, level: str = "exhigh") -> str:
        """获取封面链接
        
        Args:
            song_id: 歌曲 ID
            level: 音质等级（需要调用同一接口）
        
        Returns:
            封面 URL
        """
        try:
            info = await self.get_song_info(song_id, level)
            return info.cover
        except Exception:
            return ""


# 全局 API 实例
_api_instance: NetEaseAPI | None = None


def get_api(base_url: str | None = None) -> NetEaseAPI:
    """获取 API 实例"""
    global _api_instance
    if _api_instance is None:
        _api_instance = NetEaseAPI(base_url or API_BASE_URL)
    return _api_instance


async def close_api():
    """关闭 API 连接"""
    global _api_instance
    if _api_instance:
        await _api_instance.close()
        _api_instance = None
