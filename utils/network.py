"""网易云音乐 API 网络请求封装"""

from typing import Any

from ..exceptions import NetEaseAPIError


METING_API = "https://api.qijieya.cn/meting/"


class NetEaseAPI:
    """网易云音乐 API 客户端（基于 Meting API）"""

    DEFAULT_TIMEOUT = 10.0

    def __init__(self):
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
        page: int = 1
    ) -> list:
        """通过 Meting API 搜索歌曲"""
        import httpx
        try:
            params = {
                "type": "search",
                "id": keywords,
                "limit": limit,
                "page": page,
                "server": "netease",
            }
            resp = await self.client.get(METING_API, params=params)
            resp.encoding = "utf-8"
            resp.raise_for_status()
            data = resp.json()

            if not isinstance(data, list):
                raise NetEaseAPIError(f"API 返回格式异常: {type(data)}")

            return data
        except httpx.HTTPError as e:
            raise NetEaseAPIError(f"HTTP 请求失败: {e}") from e

    async def get_song_url(self, song_id: int, br: str = "320") -> str:
        """通过 Meting API 获取歌曲播放链接（302 重定向）

        Args:
            song_id: 歌曲 ID
            br: 音质参数，可选 2000/320/192/128

        Returns:
            歌曲播放 URL
        """
        if not song_id:
            raise NetEaseAPIError("歌曲 ID 为空")

        url = f"{METING_API}?type=url&id={song_id}&server=netease&br={br}"
        try:
            resp = await self.client.get(url, follow_redirects=False)
            if resp.status_code in (301, 302, 303, 307, 308):
                redirect_url = resp.headers.get("location")
                if redirect_url:
                    return redirect_url
            resp.raise_for_status()
            return url
        except Exception as e:
            raise NetEaseAPIError(f"获取歌曲链接失败: {e}") from e

    async def get_cover_url(self, pic_id: int, cover: str = "500") -> str:
        """通过 Meting API 获取封面真实链接（302 重定向）

        Args:
            pic_id: 封面 ID
            cover: 封面分辨率，默认 500，可选 150/300/500/800

        Returns:
            封面 URL
        """
        if not pic_id:
            return ""

        url = f"{METING_API}?type=pic&id={pic_id}&server=netease&cover={cover}"
        try:
            resp = await self.client.get(url, follow_redirects=False)
            if resp.status_code in (301, 302, 303, 307, 308):
                redirect_url = resp.headers.get("location")
                if redirect_url:
                    return redirect_url
            resp.raise_for_status()
            return url
        except Exception as e:
            from ..api import core
            core.logger.error(f"获取封面链接失败: {e}")
            return url


# 全局 API 实例
_api_instance: NetEaseAPI | None = None


def get_api() -> NetEaseAPI:
    """获取 API 实例"""
    global _api_instance
    if _api_instance is None:
        _api_instance = NetEaseAPI()
    return _api_instance


async def close_api():
    """关闭 API 连接"""
    global _api_instance
    if _api_instance:
        await _api_instance.close()
        _api_instance = None
