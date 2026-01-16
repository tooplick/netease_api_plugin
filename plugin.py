"""网易云音乐点歌插件"""

from typing import Literal, Optional
from urllib.parse import quote

from pydantic import Field
from nekro_agent.api.plugin import NekroPlugin, SandboxMethodType, ConfigBase
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.api import core

from .search import search_song, get_song_info
from .utils.network import get_api, close_api
from .exceptions import NetEaseAPIError


# 创建插件实例
plugin = NekroPlugin(
    name="网易云点歌",
    module_name="netease_api_plugin",
    description="给予AI助手通过网易云音乐搜索并发送音乐消息的能力",
    version="1.2.0",
    author="GeQian",
    url="https://github.com/tooplick/netease_api_plugin",
)


@plugin.mount_config()
class NetEasePluginConfig(ConfigBase):
    """网易云音乐插件配置项"""
    
    cover_size: Literal["0", "150", "300", "500", "800"] = Field(
        default="500",
        title="专辑封面尺寸",
        description="发送封面图片的尺寸，0 表示不发送封面",
    )
    
    audio_quality: Literal["standard", "exhigh", "lossless", "hires", "jymaster"] = Field(
        default="hires",
        title="音质选择",
        description="standard=标准, exhigh=极高, lossless=无损, hires=Hi-Res, jymaster=超清母带",
    )
    
    enable_json_card: bool = Field(
        default=True,
        title="启用音乐卡片",
        description="使用网易云音乐JSON卡片发送歌曲信息（失败时自动降级）",
    )
    
    use_external_player: bool = Field(
        default=False,
        title="卡片链接使用外部播放器",
        description="开启后，音乐卡片的主链接将跳转到外部播放器而非网易云官网",
    )
    
    external_player_url: str = Field(
        default="player.ygking.top",
        title="外部播放器地址",
        description="外部播放器的域名地址",
    )


config: NetEasePluginConfig = plugin.get_config(NetEasePluginConfig)


@plugin.mount_init_method()
async def init_plugin():
    """初始化插件"""
    core.logger.info("网易云点歌插件正在初始化...")
    # 使用 kxzjoker API
    get_api("https://api.kxzjoker.cn")
    core.logger.success("网易云点歌插件初始化完成，API 地址: https://api.kxzjoker.cn")


@plugin.mount_cleanup_method()
async def cleanup_plugin():
    """清理插件资源"""
    core.logger.info("网易云点歌插件正在清理...")
    await close_api()
    core.logger.success("网易云点歌插件清理完成")


def parse_chat_key(chat_key: str) -> tuple[str, str, int]:
    """解析 chat_key"""
    parts = chat_key.split("-", 1)
    adapter = parts[0]
    chat_info = parts[1] if len(parts) > 1 else ""
    
    if "_" in chat_info:
        chat_type, target_id_str = chat_info.rsplit("_", 1)
        target_id = int(target_id_str)
    else:
        chat_type = chat_info
        target_id = 0
    
    return adapter, chat_type, target_id


async def send_message(bot, chat_type: str, target_id: int, message) -> bool:
    """发送消息到指定会话"""
    try:
        if chat_type == "private":
            await bot.send_private_msg(user_id=target_id, message=message)
        elif chat_type == "group":
            await bot.send_group_msg(group_id=target_id, message=message)
        return True
    except Exception as e:
        core.logger.error(f"发送消息失败: {e}")
        return False


def clean_text(text: str) -> str:
    """清理文本中的无效 Unicode 字符（如私用区字符、代理对、控制字符等）"""
    if not text:
        return text
    
    cleaned = []
    for char in text:
        code = ord(char)
        # 1. 移除私用区字符 (U+E000-U+F8FF, U+F0000-U+FFFFD, U+100000-U+10FFFD)
        if (0xE000 <= code <= 0xF8FF or 
            0xF0000 <= code <= 0xFFFFD or
            0x100000 <= code <= 0x10FFFD):
            continue
            
        # 2. 移除代理对字符 (U+D800-U+DFFF)
        if 0xD800 <= code <= 0xDFFF:
            continue
            
        # 3. 移除控制字符 (U+0000-U+001F, U+007F)
        # 保留换行符等可能需要的格式字符视情况而定，但 URL 参数中最好都去除
        if code <= 0x1F or code == 0x7F:
            continue
            
        cleaned.append(char)
        
    return ''.join(cleaned)


def build_jump_url(
    song_id: int,
    song_name: str,
    artist: str,
    cover_url: str,
    music_url: str
) -> str:
    """根据配置生成跳转 URL"""
    if config.use_external_player:
        # 使用外部播放器
        base_url = config.external_player_url.rstrip("/")
        # 简单验证 base_url 格式
        if not base_url or len(base_url) > 200 or any(ord(c) > 127 for c in base_url):
             # 如果配置的 URL 异常，回退到默认
             core.logger.warning(f"检测到异常的外部播放器 URL 配置: {base_url}，已回退到默认")
             base_url = "player.ygking.top"

        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        
        # 清理无效字符并构建 URL 参数
        clean_title = clean_text(str(song_name))
        clean_artist = clean_text(str(artist))
        
        # 调试日志
        if clean_title != str(song_name):
             core.logger.debug(f"标题已清理: {repr(song_name)} -> {repr(clean_title)}")
             
        # 确保编码为 UTF-8
        try:
            quoted_title = quote(quote(clean_title, encoding='utf-8', safe=''), safe='')
            quoted_artist = quote(quote(clean_artist, encoding='utf-8', safe=''), safe='')
            quoted_cover = quote(str(cover_url), encoding='utf-8', safe='')
            quoted_audio = quote(str(music_url), encoding='utf-8', safe='')
            quoted_detail = quote(f'https://music.163.com/#/song?id={song_id}', encoding='utf-8', safe='')
        except Exception as e:
            core.logger.error(f"URL 参数编码失败: {e}")
            return f"https://music.163.com/#/song?id={song_id}"

        params = [
            f"title={quoted_title}",
            f"artist={quoted_artist}",
            f"cover={quoted_cover}",
            f"audio={quoted_audio}",
            f"detail={quoted_detail}"
        ]
        return f"{base_url}/?{'&'.join(params)}"
    else:
        # 使用网易云官网
        return f"https://music.163.com/#/song?id={song_id}"


async def get_signed_ark_card(
    song_id: int,
    song_name: str,
    artist: str,
    cover_url: str,
    music_url: str
) -> Optional[str]:
    """通过 API 获取签名的网易云音乐 JSON Ark 卡片数据"""
    import httpx
    
    try:
        # 根据配置生成跳转 URL
        jump_url = build_jump_url(song_id, song_name, artist, cover_url, music_url)
        
        data = {
            "url": music_url,
            "jump": jump_url,
            "song": song_name,
            "singer": artist,
            "cover": cover_url if cover_url else "",
            "format": "163"
        }
        
        api_url = "https://oiapi.net/api/QQMusicJSONArk"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(api_url, data=data)
            if resp.status_code == 200:
                resp_json = resp.json()
                if resp_json.get("code") == 1 and resp_json.get("message"):
                    return resp_json["message"]
                else:
                    core.logger.warning(f"获取 Ark 卡片失败: {resp_json}")
            else:
                core.logger.warning(f"Ark API 请求失败: {resp.status_code}")
    except Exception as e:
        core.logger.warning(f"获取 Ark 卡片出错: {e}")
    return None


@plugin.mount_sandbox_method(
    SandboxMethodType.AGENT,
    "send_netease_music",
    "搜索网易云音乐并发送歌曲"
)
async def send_netease_music(
    _ctx: AgentCtx,
    chat_key: str,
    keyword: str
) -> str:
    """搜索网易云歌曲并发送给用户（音乐卡片或文字+封面+语音）

    Args:
        chat_key (str): 会话标识，例如 "onebot_v11-private_12345678" 或 "onebot_v11-group_12345678"
        keyword (str): 搜索关键词：歌曲名 歌手名

    Returns:
        str: 发送结果提示信息，例如 "歌曲《晴天》已发送"

    Example:
        >>> send_netease_music("onebot_v11-group_123456", "周杰伦 晴天")
        "歌曲《晴天》已发送"
        点击音乐卡片封面即可播放歌曲
    """
    try:
        core.logger.info(f"正在搜索网易云音乐: {keyword}")
        
        # 1. 通过 API 搜索歌曲
        song = await search_song(keyword)
        song_id = song.get("id")
        song_name = song.get("name", "未知歌曲")
        artists = song.get("artists", "未知")
        
        core.logger.info(f"找到歌曲: {song_name} - {artists} (ID: {song_id})")
        
        # 2. 获取歌曲完整信息（URL、封面等）
        song_info = await get_song_info(song_id, config.audio_quality)
        song_url = song_info.url
        cover_url = song_info.cover
        # 使用 API 返回的歌手信息（更准确）
        if song_info.artist:
            artists = song_info.artist
        
        core.logger.info(f"获取到播放链接: {song_url[:50]}... (音质: {song_info.level})")
        
        # 4. 解析 chat_key 并获取 bot
        adapter, chat_type, target_id = parse_chat_key(chat_key)
        
        if adapter != "onebot_v11":
            return f"暂不支持适配器: {adapter}"
        
        bot = await _ctx.get_onebot_v11_bot()
        if not bot:
            return "无法获取 Bot 实例"
        
        # 5. 尝试发送音乐卡片
        card_sent = False
        if config.enable_json_card:
            core.logger.info(f"尝试获取并发送 JSON 卡片: {song_name}")
            json_payload = await get_signed_ark_card(
                song_id, song_name, artists, cover_url, song_url
            )
            
            if json_payload:
                from nonebot.adapters.onebot.v11 import MessageSegment
                json_msg = MessageSegment.json(json_payload)
                if await send_message(bot, chat_type, target_id, json_msg):
                    card_sent = True
                    core.logger.success("JSON 卡片发送成功")
                else:
                    core.logger.warning("JSON 卡片发送失败，降级为普通消息")
            else:
                core.logger.warning("获取 JSON 卡片数据失败，降级为普通消息")
        
        # 6. 卡片发送成功直接返回
        if card_sent:
            return f"歌曲《{song_name}》卡片已发送"
        
        # 7. 降级：发送文字 + 封面 + 语音
        info_text = f"{song_name} - {artists}"
        await send_message(bot, chat_type, target_id, info_text)
        
        # 发送封面
        cover_size = int(config.cover_size)
        if cover_size > 0 and cover_url:
            # 替换封面尺寸参数
            if "?param=" in cover_url:
                # 替换已有的尺寸参数
                import re
                sized_cover = re.sub(r'\?param=\d+y\d+', f'?param={cover_size}y{cover_size}', cover_url)
            else:
                sized_cover = f"{cover_url}?param={cover_size}y{cover_size}"
            from nonebot.adapters.onebot.v11 import MessageSegment
            cover_msg = MessageSegment.image(sized_cover)
            await send_message(bot, chat_type, target_id, cover_msg)
        
        # 发送语音
        if song_url:
            from nonebot.adapters.onebot.v11 import MessageSegment
            audio_msg = MessageSegment.record(song_url)
            await send_message(bot, chat_type, target_id, audio_msg)
        
        return f"歌曲《{song_name}》已以(文字+封面+语音)方式发送"
        
    except NetEaseAPIError as e:
        core.logger.error(f"网易云 API 错误: {e}")
        return f"点歌失败: {e.message}"
    except Exception as e:
        core.logger.error(f"点歌失败: {e}")
        return f"点歌失败: {str(e)}"
