# 网易云点歌插件

[![Nekro Agent](https://img.shields.io/badge/Nekro%20Agent-Plugin-blue)](https://github.com/KroMiose/nekro-agent)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![Version](https://img.shields.io/badge/Version-1.2.0-orange)](https://github.com/tooplick/netease_api_plugin)

为 [Nekro Agent](https://github.com/KroMiose/nekro-agent) 提供网易云音乐点歌能力的插件。

## ✨ 功能

- 🔍 **搜索歌曲** - 通过关键词搜索网易云音乐
- 🎴 **音乐卡片** - 支持 JSON Ark 卡片格式发送
- 🎵 **语音消息** - 发送歌曲语音消息（卡片失败时自动降级）
- 🖼️ **专辑封面** - 获取并发送专辑封面
- 🔗 **外部播放器** - 支持卡片跳转到自定义播放器（优化QQ桌面端体验）
- 📈 **音质自动降级** - 当高音质不可用时自动尝试次级音质

## ⚙️ 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `cover_size` | `500` | 封面尺寸 (0/150/300/500/800)，0 表示不发送封面 |
| `audio_quality` | `hires` | 音质选择，支持自动降级 |
| `enable_json_card` | `true` | 启用音乐卡片（失败时自动降级为文字+封面+语音） |
| `use_external_player` | `false` | 卡片链接使用外部播放器 |
| `external_player_url` | `player.ygking.top` | 外部播放器地址 |

### 音质等级说明

| 音质参数 | 说明 |
|----------|------|
| `standard` | 标准音质 |
| `exhigh` | 极高音质 |
| `lossless` | 无损音质 |
| `hires` | Hi-Res 高解析度 |
| `jymaster` | 超清母带 |

> **自动降级机制**: 当所选音质不可用时，插件会自动按 `jymaster → hires → lossless → exhigh → standard` 顺序尝试次级音质。

## 📖 使用

AI 会自动调用 `send_netease_music` 方法：

```python
/exec send_netease_music("onebot_v11-group_123456", "红蔷薇白玫瑰")
# 返回: "歌曲《红蔷薇白玫瑰》卡片已发送"
```

或通过自然对话触发：
> 用户: 播放红蔷薇白玫瑰

## 📁 目录结构

```
netease_api_plugin/
├── __init__.py          # 插件入口
├── plugin.py            # 主插件逻辑
├── search.py            # 搜索/获取音频/封面 API
├── utils/
│   ├── __init__.py
│   └── network.py       # HTTP 客户端 & API 封装
└── exceptions/
    └── __init__.py      # 自定义异常
```

## 🔌 API 来源

- **搜索/音频/封面**: [Kxzjoker API](https://api.kxzjoker.cn)
- **卡片签名**: [OiAPI](https://oiapi.net/)

## 📋 更新日志

### v1.2.0
- 🆕 新增 `audio_quality` 配置项，支持 5 种音质选择
- 🆕 新增音质自动降级机制
- 🔄 迁移至 Kxzjoker API
- 🔧 优化 `SongInfo` 数据结构，合并歌曲信息获取逻辑
- 🔧 改进 URL 编码处理，修复特殊字符兼容性问题

### v1.1.0
- 🆕 新增外部播放器支持 (`use_external_player`, `external_player_url`)
- 🆕 新增 JSON Ark 音乐卡片功能
- 🔧 优化消息降级策略

### v1.0.0
- 🎉 初始版本发布

## 👤 作者

[tooplick](https://github.com/tooplick)

## 📄 许可证

MIT License