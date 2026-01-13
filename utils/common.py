"""通用工具函数"""

from typing import Any


def format_artists(artists: list[dict[str, Any]]) -> str:
    """格式化歌手名称列表
    
    Args:
        artists: 歌手信息列表，每个包含 'name' 字段
    
    Returns:
        用 "/" 连接的歌手名称字符串
    """
    return "/".join(artist.get("name", "未知") for artist in artists)


def format_duration(milliseconds: int) -> str:
    """格式化时长（毫秒转为 mm:ss）
    
    Args:
        milliseconds: 时长（毫秒）
    
    Returns:
        格式化的时长字符串 (mm:ss)
    """
    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def get_song_info_text(song: dict[str, Any]) -> str:
    """获取歌曲信息文本
    
    Args:
        song: 歌曲信息字典
    
    Returns:
        格式化的歌曲信息文本
    """
    name = song.get("name", "未知歌曲")
    artists = format_artists(song.get("ar", []) or song.get("artists", []))
    album = song.get("al", {}).get("name", "") or song.get("album", {}).get("name", "")
    duration = format_duration(song.get("dt", 0) or song.get("duration", 0))
    
    text = f"🎵 {name}\n"
    text += f"🎤 歌手: {artists}\n"
    if album:
        text += f"💿 专辑: {album}\n"
    text += f"⏱️ 时长: {duration}"
    
    return text


def get_cover_url(song: dict[str, Any], size: int = 300) -> str:
    """获取专辑封面 URL
    
    Args:
        song: 歌曲信息字典
        size: 封面尺寸
    
    Returns:
        封面 URL
    """
    album = song.get("al", {}) or song.get("album", {})
    pic_url = album.get("picUrl", "")
    if pic_url and size:
        return f"{pic_url}?param={size}y{size}"
    return pic_url
