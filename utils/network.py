"""网易云音乐 API 网络请求封装"""

import httpx
from typing import Any

from ..exceptions import NetEaseAPIError


class NetEaseAPI:
    """网易云音乐 API 客户端"""
    
    DEFAULT_TIMEOUT = 10.0
    
    def __init__(self, base_url: str = "https://music-api.focalors.ltd"):
        """初始化 API 客户端
        
        Args:
            base_url: API 服务基础地址
        """
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端实例"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.DEFAULT_TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._client
    
    async def close(self):
        """关闭客户端连接"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """发送 API 请求
        
        Args:
            endpoint: API 端点路径
            params: 请求参数
        
        Returns:
            API 响应数据
        
        Raises:
            NetEaseAPIError: 请求失败时抛出
        """
        try:
            resp = await self.client.get(endpoint, params=params or {})
            resp.raise_for_status()
            data = resp.json()
            
            # 检查 API 返回码
            code = data.get("code", 200)
            if code != 200:
                raise NetEaseAPIError(f"API 返回错误: code={code}", data)
            
            return data
        except httpx.HTTPError as e:
            raise NetEaseAPIError(f"HTTP 请求失败: {e}") from e
    
    async def search(
        self, 
        keywords: str, 
        type: int = 1, 
        limit: int = 1,
        offset: int = 0
    ) -> dict:
        """搜索歌曲
        
        Args:
            keywords: 搜索关键词
            type: 搜索类型 (1=歌曲, 10=专辑, 100=歌手, 1000=歌单)
            limit: 返回数量
            offset: 偏移量
        
        Returns:
            搜索结果
        """
        return await self.request("/cloudsearch", {
            "keywords": keywords,
            "type": type,
            "limit": limit,
            "offset": offset
        })
    
    async def song_detail(self, ids: list[int]) -> dict:
        """获取歌曲详情
        
        Args:
            ids: 歌曲 ID 列表
        
        Returns:
            歌曲详情
        """
        return await self.request("/song/detail", {
            "ids": ",".join(map(str, ids))
        })
    
    async def song_url(self, ids: list[int], level: str = "standard") -> dict:
        """获取歌曲播放链接
        
        Args:
            ids: 歌曲 ID 列表
            level: 音质等级 (standard, higher, exhigh, lossless, hires)
        
        Returns:
            包含播放链接的响应
        """
        return await self.request("/song/url/v1", {
            "id": ",".join(map(str, ids)),
            "level": level
        })


# 全局 API 实例
_api_instance: NetEaseAPI | None = None


def get_api(base_url: str | None = None) -> NetEaseAPI:
    """获取 API 实例
    
    Args:
        base_url: 可选的 API 基础地址，首次调用时设置
    
    Returns:
        NetEaseAPI 实例
    """
    global _api_instance
    if _api_instance is None:
        _api_instance = NetEaseAPI(base_url or "https://music-api.focalors.ltd")
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
