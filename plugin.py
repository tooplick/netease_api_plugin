"""网易云音乐点歌插件"""

from typing import Literal, Optional
from urllib.parse import quote

from pydantic import Field
from nekro_agent.api.plugin import NekroPlugin, SandboxMethodType, ConfigBase
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.api import core

from .search import search_song, get_song_url, get_cover_url
from .utils.network import get_api, close_api
from .exceptions import NetEaseAPIError


# 创建插件实例
plugin = NekroPlugin(
    name="网易云点歌",
    module_name="netease_api_plugin",
    description="给予AI助手通过网易云音乐搜索并发送音乐消息的能力",
    version="1.1.0",
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
    # 使用固定的 API 地址
    get_api("https://163api.qijieya.cn")
    core.logger.success("网易云点歌插件初始化完成，API 地址: https://163api.qijieya.cn")


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
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        
        # 构建外部播放器 URL 参数（显式使用 UTF-8 编码）
        params = [
            f"title={quote(str(song_name), encoding='utf-8', safe='')}",
            f"artist={quote(str(artist), encoding='utf-8', safe='')}",
            f"cover={quote(str(cover_url), encoding='utf-8', safe='')}",
            f"audio={quote(str(music_url), encoding='utf-8', safe='')}",
            f"detail={quote(f'https://music.163.com/#/song?id={song_id}', encoding='utf-8', safe='')}"
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
        
        # 1. 通过网易云 API 搜索歌曲
        song = await search_song(keyword)
        song_id = song.get("id")
        song_name = song.get("name", "未知歌曲")
        artists = song.get("artists", "未知")
        
        core.logger.info(f"找到歌曲: {song_name} - {artists} (ID: {song_id})")
        
        # 2. 通过 NodeJS API 获取完整播放链接
        song_url = await get_song_url(song_id)
        core.logger.info(f"获取到播放链接: {song_url[:50]}...")
        
        # 3. 通过 Meting API 获取封面
        cover_url = await get_cover_url(song_id)
        if cover_url:
            core.logger.info(f"获取到封面链接")
        
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
