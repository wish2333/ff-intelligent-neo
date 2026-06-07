# 更新记录 v2.2.5

- 日期: 2026-06-07
- 分支: dev-2.2.4
- 类型: 修复 (fix) + 功能 (feat)

---

## 变更概述

修复音视频混流页字幕功能的 map 索引错误，新增字幕压制模式（Burn Mode），支持将 ASS 特效字幕烧录到视频中。

## 问题背景

用户在音视频混流页选择字幕文件后执行任务时，FFmpeg 报错：

```
Invalid input file index: 2.
Failed to set value '2:s' for option 'map': Invalid argument
```

根因分析发现三个问题：
1. **map 索引硬编码**: 代码始终使用 `-map 2:s`，但当没有外挂音频时字幕实际是 input #1
2. **仅支持软嵌入**: 当前只支持将字幕作为独立轨道嵌入容器（`-c:s mov_text`），无法压制 ASS 特效字幕
3. **缺少模式选择**: UI 没有提供字幕处理模式的选择

## 变更详情

### 1. 修复 embed 模式 map 索引计算 (BUG FIX)

**文件**: `core/command_builder.py`

- 原: 硬编码 `map_directives.extend(["-map", "2:s", ...])`
- 新: 动态计算 `sub_idx`，无外挂音频时为 `1:s`，有外挂音频时为 `2:s`

```python
sub_idx = 1  # input #0 is video
if avsmix.external_audio_path:
    sub_idx = 2  # input #1 is external audio
map_directives.extend(["-map", f"{sub_idx}:s", "-c:s", "mov_text"])
```

### 2. 新增 subtitle_mode 字段 (FEATURE)

**文件**: `core/models.py`, `frontend/src/types/config.ts`, `frontend/src/composables/useGlobalConfig.ts`

- `AudioSubtitleConfig` 新增 `subtitle_mode: str = "embed"` 字段
- 可选值: `"embed"`（软字幕嵌入）或 `"burn"`（压制到画面）
- `from_dict()` 使用 `.get("subtitle_mode", "embed")` 保证向后兼容已保存的配置

### 3. 实现 burn 模式命令构建 (FEATURE)

**文件**: `core/command_builder.py`

新增三个辅助函数:

- `_ffmpeg_filter_escape_path(path)`: 转义路径用于 FFmpeg 滤镜语法
  - `\` → `/`（跨平台兼容）
  - `'` → `'\\''`（处理路径中的单引号）
  - `:` → `\:`（转义 FFmpeg 滤镜分隔符）
  - 外层用单引号包裹
- `_inject_subtitle_burn_filter(filter_args, burn_filter)`: 将字幕滤镜注入已有的 filter_args
  - 有 `-vf` 时追加到链尾
  - 有 `-filter_complex`（水印）时插入到 overlay 之前的视频链中
  - 无滤镜时新建 `-vf`
- `_remove_copy_codec_pair(args, codec_flag)`: 移除 `-c:v copy` 键值对，因为 burn 模式强制需要重新编码

burn 模式生成的命令示例:
```
ffmpeg -i input.mp4 -c:v av1_nvenc -c:a aac -vf subtitles='Q\:/path/to/sub.ass' -y output.mp4
```

### 4. burn 模式 + copy 编码器冲突校验 (SAFETY)

**文件**: `core/command_builder.py`

- `validate_config` 新增校验: burn 模式 + `video_codec == "copy"` → 警告提示
- 命令构建时自动移除 `-c:v copy`，确保视频被正确重新编码

### 5. 新增字幕模式选择 UI (FEATURE)

**文件**: `frontend/src/pages/AudioSubtitlePage.vue`

- 字幕文件选择后显示模式单选按钮:
  - "嵌入（软字幕）" — 将字幕作为独立轨道嵌入，播放时可开关
  - "压制（内嵌字幕）" — 将特效字幕烧录到画面中，需要重新编码
- burn 模式下自动隐藏语言代码字段（不适用）

### 6. 国际化文本 (FEATURE)

**文件**: `frontend/src/i18n/locales/zh-CN.ts`, `frontend/src/i18n/locales/en.ts`

新增翻译键:
- `avMix.subtitle.mode`: 字幕模式 / Subtitle Mode
- `avMix.subtitle.modeEmbed`: 嵌入（软字幕） / Embed (Soft Subtitle)
- `avMix.subtitle.modeEmbedHint`: 将字幕作为独立轨道嵌入容器，可开关显示
- `avMix.subtitle.modeBurn`: 压制（内嵌字幕） / Burn (Hardcode)
- `avMix.subtitle.modeBurnHint`: 将特效字幕烧录到画面中，需要重新编码视频

### 7. 简化 build_avsmix_command (REFACTOR)

**文件**: `core/command_builder.py`

- `build_avsmix_command()` 原实现与 `build_command()` 存在重复逻辑且从未被外部调用
- 简化为直接委托 `build_command()`，该函数已原生处理 avsmix 的所有模式

### 8. 字段文档更新

**文件**: `docs/fields/AudioSubtitleConfig.csv`

- 新增 `subtitle_mode` 字段定义

---

## 变更文件清单

| 文件 | 变更类型 |
|------|----------|
| `core/models.py` | 新增字段 |
| `core/command_builder.py` | 修复 + 新增 + 重构 |
| `frontend/src/types/config.ts` | 新增字段 |
| `frontend/src/composables/useGlobalConfig.ts` | 新增默认值 |
| `frontend/src/pages/AudioSubtitlePage.vue` | UI 新增 |
| `frontend/src/i18n/locales/zh-CN.ts` | 文案新增 |
| `frontend/src/i18n/locales/en.ts` | 文案新增 |
| `docs/fields/AudioSubtitleConfig.csv` | 文档更新 |

---

## Commit Message

```
fix: 修复字幕 map 索引错误，新增字幕压制模式

- 修复 embed 模式 map 索引硬编码为 2:s 的 bug，改为动态计算
- 新增 subtitle_mode 字段，支持 embed（软字幕）和 burn（压制）两种模式
- burn 模式使用 FFmpeg subtitles 滤镜将特效字幕烧录到画面中
- burn 模式自动移除 -c:v copy 以确保视频重新编码
- 新增 _ffmpeg_filter_escape_path 处理 Windows 路径中的特殊字符
- 新增 _inject_subtitle_burn_filter 支持与现有滤镜链（裁剪/水印等）组合
- 简化 build_avsmix_command 委托给 build_command 避免重复逻辑
```

---

## 验证结果

### 命令构建测试

| 场景 | 生成的关键参数 | 状态 |
|------|----------------|------|
| burn 模式 | `-vf subtitles='Q\:/test.ass'` | 正确 |
| embed 模式（无音频） | `-map 1:s -c:s mov_text` | 正确（原为 2:s） |
| embed 模式 + 外挂音频 | `-map 0:v -map 1:a -map 2:s` | 正确 |
| burn + copy 编码器 | `-c:v copy` 已移除，仅保留 `-vf` | 正确 |
| burn + 音频 + copy | `-vf subtitles=... -map 0:v -map 1:a` | 正确 |

### 构建验证

- 前端 `bun run build`: 通过
- 后端 `from core.command_builder import *`: 导入成功
