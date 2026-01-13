"""网易云音乐 API 网络请求封装"""

import httpx
from typing import Any

from ..exceptions import NetEaseAPIError


class NetEaseAPI:
    """网易云音乐 API 客户端"""
    
    DEFAULT_TIMEOUT = 10.0
    
    # Meting API（用于获取封面）
    METING_API = "https://api.qijieya.cn/meting/"
    
    def __init__(self, base_url: str = "https://163api.qijieya.cn"):
        """初始化 API 客户端
        
        Args:
            base_url: 网易云 NodeJS API 服务基础地址
        """
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端实例"""
        if self._client is None or self._client.is_closed:
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
        type: int = 1, 
        limit: int = 1,
        offset: int = 0
    ) -> dict:
        """通过网易云 API 搜索歌曲"""
        try:
            url = f"{self.base_url}/cloudsearch"
            params = {
                "keywords": keywords,
                "type": type,
                "limit": limit,
                "offset": offset
            }
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            code = data.get("code", 200)
            if code != 200:
                raise NetEaseAPIError(f"API 返回错误: code={code}", data)
            
            return data
        except httpx.HTTPError as e:
            raise NetEaseAPIError(f"HTTP 请求失败: {e}") from e

    async def get_song_url(self, song_id: int) -> str:
        """通过 NodeJS API 获取歌曲播放链接（完整歌曲）
        
        和原项目 ncm_nodejs.py 一致：使用 /song/url?id=xxx
        
        Args:
            song_id: 歌曲 ID
        
        Returns:
            歌曲播放 URL
        """
        try:
            url = f"{self.base_url}/song/url"
            params = {"id": song_id}
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            result = resp.json()
            
            data = result.get("data", [])
            if data and len(data) > 0:
                audio_url = data[0].get("url")
                if audio_url:
                    return audio_url
            
            raise NetEaseAPIError(f"未获取到歌曲链接")
        except NetEaseAPIError:
            raise
        except httpx.HTTPError as e:
            raise NetEaseAPIError(f"HTTP 请求失败: {e}") from e
        except Exception as e:
            raise NetEaseAPIError(f"获取歌曲链接失败: {e}") from e

    async def get_cover_url(self, song_id: int) -> str:
        """通过 Meting API 获取封面链接（跟随重定向获取真实 URL）
        
        Args:
            song_id: 歌曲 ID
        
        Returns:
            封面真实 URL（网易云 CDN 地址）
        """
        try:
            url = f"{self.METING_API}?type=song&id={song_id}"
            resp = await self.client.get(url)
            resp.raise_for_status()
            result = resp.json()
            
            if isinstance(result, list) and len(result) > 0:
                pic_redirect = result[0].get("pic", "")
                if pic_redirect:
                    # 跟随重定向获取真实封面 URL
                    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as redirect_client:
                        pic_resp = await redirect_client.get(pic_redirect)
                        # 返回最终 URL
                        return str(pic_resp.url)
            
            return ""
        except Exception as e:
            # 封面获取失败不抛异常，返回空字符串
            return ""


# 全局 API 实例
_api_instance: NetEaseAPI | None = None


def get_api(base_url: str | None = None) -> NetEaseAPI:
    """获取 API 实例"""
    global _api_instance
    if _api_instance is None:
        _api_instance = NetEaseAPI(base_url or "https://163api.qijieya.cn")
    return _api_instance


def set_api_base_url(base_url: str):
    """设置 API 基础地址（会重新创建实例）"""
    global _api_instance
    _api_instance = NetEaseAPI(base_url)


async def close_api():
    """关闭 API 连接"""
    global _api_instance
    if _api_instance:
        await _api_instance.close()
        _api_instance = None
