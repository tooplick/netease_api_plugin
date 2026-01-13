"""网易云音乐点歌插件异常类"""


class NetEaseAPIError(Exception):
    """网易云 API 基础错误"""
    
    def __init__(self, message: str = "API 请求失败", data: dict | None = None):
        self.message = message
        self.data = data or {}
        super().__init__(self.message)


class SearchError(NetEaseAPIError):
    """搜索失败"""
    pass


class SongNotFoundError(NetEaseAPIError):
    """歌曲未找到"""
    pass


class SongUrlError(NetEaseAPIError):
    """获取歌曲链接失败"""
    pass
