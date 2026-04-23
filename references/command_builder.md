## 系统设计

### 编码器数据库设计（强烈推荐采纳）

**设计模式**：

- 建立全面的编码器注册表，包含40种视频编码器、21种音频编码器、13种图片编码器
- 每个编码器附带推荐的质量值、适用场景、使用建议

**关键优势**：

1. **丰富的编码器选择**：用户可以从预定义列表中选择，避免记忆复杂的编码器名称
2. **质量值推荐**：为每个编码器提供推荐的CRF/CQ值，帮助用户快速设置合理参数
3. **使用场景标注**：标注每个编码器的适用场景（日常推荐、专业用途、不推荐）
4. **自定义参数支持**：未暴露在GUI的FFmpeg功能可通过自定义参数输入使用

**ff-intelligent应用建议**：

```typescript
// encoder-registry.ts
interface EncoderConfig {
  name: string              // FFmpeg编码器名称（如：libx264）
  displayName: string        // 用户友好的显示名称（如：H.264/AVC）
  category: 'video' | 'audio' | 'image'
  hardwareType?: 'cpu' | 'nvidia' | 'amd' | 'intel'
  recommendedQuality?: number // 推荐的质量值（CRF/CQ）
  qualityMode?: 'crf' | 'cq' | 'qp' | 'global_quality'
  description: string       // 编码器描述和使用建议
  pros: string[]           // 优点列表
  cons: string[]           // 缺点列表
  usageScenarios: string[] // 适用场景
  notRecommended?: boolean   // 是否不推荐日常使用
}

// 编码器配置示例
const VIDEO_ENCODERS: EncoderConfig[] = [
  {
    name: 'libx264',
    displayName: 'H.264/AVC',
    category: 'video',
    hardwareType: 'cpu',
    recommendedQuality: 23,
    qualityMode: 'crf',
    description: '经典编码器，兼容性最好',
    pros: ['兼容性极佳', '解码广泛支持'],
    cons: ['已过时', '压缩效率不如H.265'],
    usageScenarios: ['日常推荐', '兼容老设备'],
    notRecommended: false
  },
  {
    name: 'libx265',
    displayName: 'H.265/HEVC',
    category: 'video',
    hardwareType: 'cpu',
    recommendedQuality: 24,
    qualityMode: 'crf',
    description: '目前的最佳选择，压制组首选',
    pros: ['压缩效率高', '质量优秀'],
    cons: ['编码速度较慢', '解码需要较新硬件'],
    usageScenarios: ['日常强烈推荐', '首选'],
    notRecommended: false
  },
  {
    name: 'h264_nvenc',
    displayName: 'H.264/AVC (NVIDIA)',
    category: 'video',
    hardwareType: 'nvidia',
    recommendedQuality: 28,
    qualityMode: 'cq',
    description: 'RTX 40系及以上推荐',
    pros: ['编码速度快', '多线程优化'],
    cons: ['需要NVIDIA显卡', '质量略低于CPU'],
    usageScenarios: ['日常强烈推荐'],
    notRecommended: false
  },
  {
    name: 'h264_amf',
    displayName: 'H.264/AVC (AMD)',
    category: 'video',
    hardwareType: 'amd',
    recommendedQuality: 34,
    qualityMode: 'qp',
    description: '7000系独显开始支持',
    pros: ['AMD硬件加速'],
    cons: ['不推荐日常使用', '质量一般'],
    usageScenarios: ['不推荐日常使用'],
    notRecommended: true
  }
]
```

---

### 预设系统（强烈推荐采纳）

**设计模式**：

- 所有编码任务使用参数快照，在任务添加到队列时创建，而非执行时
- 任务一旦添加，参数即锁定，防止竞态条件
- 预设文件包含完整的参数配置，可共享和复用

**关键优势**：

1. **批量处理一致性**：预设确保批量任务使用相同的参数
2. **参数锁定机制**：防止用户在任务等待时修改参数导致的不一致
3. **配置共享**：预设文件可导出分享给他人或备份

**ff-intelligent应用建议**：

```typescript
// preset-system.ts
interface Preset {
  id: string                    // 唯一标识符（UUID）
  name: string                  // 预设名称（如：YouTube推荐）
  category: 'transcode' | 'filter' | 'merge'
  description?: string           // 预设描述
  params: FFmpegParams        // FFmpeg参数对象
  encoder: string               // 使用的编码器
  qualityValue: number         // 质量值
  bitrate?: number              // 可选的码率值
  isBuiltIn: boolean          // 是否为内置预设
  createdAt: timestamp
  updatedAt: timestamp
}

interface FFmpegParams {
  // 基础参数
  input?: string
  output?: string

  // 编码参数
  codec?: string
  crf?: number
  cq?: number
  qp?: number
  preset?: string
  profile?: string
  level?: string
  pixelFormat?: string

  // 滤镜参数
  filters?: string
  audioFilters?: string

  // 高级参数
  customArgs?: string
}

// 预设使用示例
const BUILTIN_PRESETS: Preset[] = [
  {
    id: 'youtube-recommended',
    name: 'YouTube推荐',
    category: 'transcode',
    description: '适合YouTube上传，平衡质量和大小',
    encoder: 'libx264',
    qualityValue: 23,
    isBuiltIn: true,
    params: {
      codec: 'libx264',
      crf: 23,
      preset: 'slow',
      pixelFormat: 'yuv420p',
      audioCodec: 'aac',
      audioBitrate: '192k'
    }
  },
  {
    id: 'high-quality-hevc',
    name: '高质量H.265',
    category: 'transcode',
    description: 'H.265高质量编码，适合存档',
    encoder: 'libx265',
    qualityValue: 20,
    isBuiltIn: true,
    params: {
      codec: 'libx265',
      crf: 20,
      preset: 'slow',
      pixelFormat: 'yuv420p10le'
    }
  }
]
```

---

### 自定义参数支持（推荐采纳）

**设计模式**：

- GUI中未暴露的FFmpeg功能可通过自定义参数输入使用
- 支持直接输入FFmpeg参数名和值
- 显示完整的生成命令行，保持完全透明

**关键优势**：

1. **无限的扩展性**：用户可以使用任何FFmpeg支持的参数
2. **学习桥梁**：透明显示帮助用户学习FFmpeg命令行
3. **专业需求满足**：高级用户可直接使用命令行功能

**ff-intelligent应用建议**：

- 在参数配置界面提供"高级选项"或"自定义参数"选项卡
- 支持文本输入，用户可输入原始FFmpeg参数
- 实时验证参数语法（参数名合法性）
- 命令预览区域显示完整的FFmpeg命令
- 提供参数提示和帮助链接（链接到FFmpeg官方文档）

---

### 透明操作理念（推荐采纳）

**设计理念**：

- 参数名直接匹配FFmpeg文档（如：`-crf`, `-preset`, `-pix_fmt`）
- 生成的命令行始终可见
- 用户可准确了解将要执行的操作

**ff-intelligent应用建议**：

- 所有参数配置项使用FFmpeg官方参数名（或清晰的中文映射）
- 提供命令预览窗口，实时显示生成的FFmpeg命令
- 显示每个参数的说明（工具提示）
- 允许用户直接编辑命令行（高级选项）

## 编码器推荐策略

### 推荐的编码器配置

根据README中的编码器建议，建议ff-intelligent采纳以下配置：

**首选推荐（优先展示和推荐使用）**：

- **视频编码器**：
  - `av1_nvenc` - RTX 40系及以上推荐，可超越libsvtav1（默认选用，CQ=36）
  - `libx265` - H.265/HEVC，当前最佳选择（CRF=24）
  - `libsvtav1` - AV1官方实现，Intel主导，多线程优化（CRF=32）
- **音频编码器**：
  - `aac` - 通用音频编码
  - `opus` - 开源高质量音频编码
  - `flac` - 无损音频编码
  - mp3
  - `alac` - Apple Lossless

**次选推荐（有条件推荐）**：

- `libx264` - H.264，兼容性最好但已过时
- `hevc_nvenc` - NVIDIA硬件H.265，足够日常基本需求（CQ=28）
- `libvpx-vp9` - VP9，强于264但弱于265

**不推荐日常使用（不在下拉列表中显示）**：

- `h264_amf` - AMD H.264，极其不推荐
- `h264_qsv` - Intel QSV，不推荐除非只是转码
- `hevc_amf` - AMD H.265，不推荐用于日常需求

---

### 质量值参考

**推荐的质量值（灵活调整）**：

| 编码器     | 质量值 | 说明                        | 肉眼无损 |
| ---------- | ------ | --------------------------- | -------- |
| libx264    | 23     | 均衡标准                    | 16       |
| libx265    | 24/25  | 综合推荐<br/>26用于视觉无损 | 16       |
| libsvtav1  | 32     | 综合推荐                    | 16       |
| av1_nvenc  | 36     | 综合推荐                    | 16       |
| hevc_nvenc | 28     | 综合推荐<br/>26用于视觉无损 | 16       |

**重要提示**：

- 质量值因编码器而异，需要根据具体编码器和视频内容灵活调整
- 23不一定是糊的，但16一定是清晰的
- 已被压过的视频几乎不可能再压得更小
- 硬件加速通常需要设置更大的质量值

**音频码率：**

```
128k` (default), `64k`, `192k`, `320k
```

### 支持设定目标码率、最大码率等码率主导的参数

根据FFmpeg原生命令自行构建相关支持

## 滤镜接口（推荐采纳）

**功能描述**：
VfilterInterface提供复杂的滤镜链处理，包括旋转、缩放、音频归一化等。

**核心功能**：

1. **画面变换**：旋转、翻转、缩放、裁剪
2. **音频处理**：音量归一化（loudnorm）

1. **复杂滤镜链**：支持多滤镜串联，并支持用户自定义输入
2. **高级滤镜**：动态模糊、超分辨率、色彩管理

**ff-intelligent应用建议**：

- V1.0基础滤镜支持（旋转、裁剪、音量调整）
- V1.1或V2.0支持复杂滤镜链
- V2.0支持高级滤镜（动态模糊、超分辨率等）

### Audio Normalization Feature

The VfilterInterface includes audio normalization as an "extra feature" beyond video filtering. This applies FFmpeg's `loudnorm` filter to standardize audio levels:

| Filter     | Parameter | Description                       |
| ---------- | --------- | --------------------------------- |
| `loudnorm` | `I=-16`   | Integrated loudness target (LUFS) |
| `loudnorm` | `TP=-1.5` | True peak limit (dBTP)            |
| `loudnorm` | `LRA=11`  | Loudness range target (LU)        |

### Accelerated_Encode Method

The `accelerated_encode` method modifies video playback speed by applying synchronized video and audio filters. This operation uses FFmpeg's `setpts` filter for video frame timestamp manipulation and `atempo` filter for audio tempo adjustment.

**Implementation**: [modules/ffmpegApi.py365-383](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L365-L383)

```
Command structure:
-filter_complex "[0:v]setpts=PTS/{rate}[v];[0:a]atempo={rate}[a]" -map "[v]" -map "[a]"
```

The filter graph performs two parallel operations:

- **Video adjustment**: `setpts=PTS/{rate}` multiplies presentation timestamps by the inverse of the rate. A rate of 2.0 halves timestamps, doubling playback speed.
- **Audio adjustment**: `atempo={rate}` stretches or compresses audio duration without changing pitch. The atempo filter has limits (0.5 to 2.0), requiring chained filters for extreme rates.

#### Rate Constraints

| Rate Range     | Effect        | Implementation                                               |
| -------------- | ------------- | ------------------------------------------------------------ |
| 0.5 - 1.0      | Slow motion   | Single atempo filter                                         |
| 1.0            | Normal speed  | Operation skipped [modules/vcodecp_Interface.py413-415](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L413-L415) |
| 1.0 - 2.0      | Fast motion   | Single atempo filter                                         |
| > 2.0 or < 0.5 | Extreme rates | Requires chained atempo filters                              |

### Audio/Video/Subtitle Mixing

#### avsmix_encode Method

The `avsmix_encode` method combines video from one file with audio and subtitles from external sources. This operation uses FFmpeg's stream mapping to select specific streams from multiple input files.

**Implementation**: [modules/ffmpegApi.py385-405](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L385-L405)

```
Command structure:
-i "{input_file}" {audio} {subtitle} {encoder} "{output_file}"
```

The `audio` and `subtitle` parameters contain additional input specifications and mapping directives. Common patterns include:

- **Audio replacement**: `-i "audio.mp3" -map 0:v -map 1:a`
- **Subtitle addition**: `-i "subtitles.srt" -c:s mov_text -metadata:s:s:0 language=eng`
- **Multiple streams**: `-i "audio.aac" -i "subs.srt" -map 0:v -map 1:a -map 2:s`

### Container Remuxing

#### remux_video Method

The `remux_video` method converts video container formats without re-encoding streams. This operation uses FFmpeg's `-c copy` codec specification to perform a lossless format change.

**Implementation**: [modules/ffmpegApi.py407-424](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L407-L424)

```
Command structure:
-i "{input_file}" -c copy "{output_file}.{format}"
```

Common format conversions:

- MP4 ↔ MKV: Matroska container with all codec support
- MP4 ↔ AVI: Legacy format conversion
- MP4 ↔ WEBM: Web-optimized format (requires VP8/VP9 or AV1 video

## Complex Filter Chains

### Filter Graph Architecture

Complex filter chains use FFmpeg's `-filter_complex` parameter to construct directed acyclic graphs (DAGs) of video and audio transformations. The application uses filter chains extensively in merge operations to normalize video properties.

**Primary use case**: [modules/ffmpegApi.py272-296](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L272-L296) - `merge_video` method

### Merge Operation Filter Graph

The `merge_video` method demonstrates comprehensive filter chain usage for concatenating three videos with property normalization:

```

```

**Filter chain breakdown** [modules/ffmpegApi.py288-289](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L288-L289):

1. **Video normalization per input**:
   - `fps={fps}`: Standardize frame rate
   - `scale={resolution}`: Standardize resolution (e.g., `1920:1080`)
   - `setsar=1`: Set Sample Aspect Ratio to 1:1 (square pixels)
2. **Audio normalization per input**:
   - `aformat`: Set sample rate to 44100 Hz and stereo channel layout
3. **Concatenation**:
   - `concat=n=3:v=1:a=1`: Join 3 segments with 1 video stream and 1 audio stream
   - Outputs: `[vout]` and `[aout]` streams
4. **Output mapping**:
   - `-map "[vout]" -map "[aout]"`: Select normalized streams for output

**Sources**: [modules/ffmpegApi.py272-296](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L272-L296)

### Two-Stream Merge Variation

The `merge_video_two` method uses identical filter architecture but with `n=2` in the concat filter [modules/ffmpegApi.py298-321](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L298-L321)

### UI Configuration for Filter Parameters

The batch processing interface allows users to specify resolution and FPS overrides for merge operations:

| UI Control            | Parameter                  | Default   | Code Reference                                               |
| --------------------- | -------------------------- | --------- | ------------------------------------------------------------ |
| `VcodecpIFcheckBox_2` | Enable resolution override | Disabled  | [modules/vcodecp_Interface.py251-266](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L251-L266) |
| `VcodecpIFlineEdit`   | Resolution value           | 1920x1080 | [modules/vcodecp_Interface.py509](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L509-L509) |
| `VcodecpIFcheckBox_3` | Enable FPS override        | Disabled  | [modules/vcodecp_Interface.py270-285](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L270-L285) |
| `VcodecpIFlineEdit_2` | FPS value                  | 30        | [modules/vcodecp_Interface.py273](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L273-L273) |

**Resolution format conversion**: UI uses `1920x1080` format, converted to FFmpeg format `1920:1080` via `.replace('x', ':')` [modules/vcodecp_Interface.py509](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L509-L509)

**Sources**: [modules/vcodecp_Interface.py505-541](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L505-L541) [modules/vcodecp_Interface.py542-608](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L542-L608)

## Filter-Specific Considerations

### setpts Filter

The `setpts` filter modifies Presentation Timestamp (PTS) values to control playback timing. The formula `PTS/{rate}` divides each frame's timestamp by the rate factor:

- Rate 2.0: PTS/2.0 → frames appear twice as fast (half the time between frames)
- Rate 0.5: PTS/0.5 = PTS*2 → frames appear twice as slow (double the time between frames)

### atempo Filter

The `atempo` filter changes audio playback speed without pitch shifting. Constraints:

- Single filter range: 0.5 to 2.0
- For rates outside this range, chain multiple atempo filters
- Example for 4x speed: `atempo=2.0,atempo=2.0`

### fps Filter

The `fps` filter changes frame rate through frame duplication or dropping:

- Upsampling (24→30): Duplicates frames proportionally
- Downsampling (60→30): Drops every other frame
- Used in merge operations to ensure consistent frame rates

### scale Filter

The `scale` filter resizes video dimensions. Syntax: `scale=width:height`

- Supports aspect ratio preservation: `scale=1920:-1` (auto-calculate height)
- Used in merge operations to ensure consistent resolution
- May introduce scaling artifacts if significant size changes occur

### setsar Filter

The `setsar` filter sets Sample Aspect Ratio (SAR):

- `setsar=1` forces square pixels (1:1 ratio)
- Prevents stretched/squashed video from mismatched SAR values
- Critical for merge operations to avoid distortion

**Sources**: [modules/ffmpegApi.py365-383](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L365-L383) [modules/ffmpegApi.py272-296](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L272-L296)

## Advanced Filter Operations Reference

### Filter Categories Available

While the codebase primarily implements specific filter chains, FFmpeg supports extensive filter categories:

**Implemented in codebase**:

- `setpts`: Video timestamp manipulation [modules/ffmpegApi.py377](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L377-L377)
- `atempo`: Audio tempo adjustment [modules/ffmpegApi.py377](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L377-L377)
- `fps`: Frame rate conversion [modules/ffmpegApi.py288](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L288-L288)
- `scale`: Resolution scaling [modules/ffmpegApi.py288](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L288-L288)
- `setsar`: Sample aspect ratio [modules/ffmpegApi.py288](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L288-L288)
- `aformat`: Audio format normalization [modules/ffmpegApi.py288](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L288-L288)
- `concat`: Stream concatenation [modules/ffmpegApi.py289](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L289-L289)

**Mentioned but not fully implemented**:

- Rotation filters [README.md103](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/README.md?plain=1#L103-L103)
- Audio normalization [README.md103](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/README.md?plain=1#L103-L103)

### Filter Complex vs Simple Filters

The codebase uses `-filter_complex` for multi-input/output filter graphs and simple filter syntax for single-stream operations:

- **filter_complex**: Required when joining streams, using multiple inputs, or creating complex DAGs [modules/ffmpegApi.py377](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L377-L377) [modules/ffmpegApi.py288-289](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L288-L289)
- **Simple filters**: Could be used for single-stream operations (not extensively used in codebase)

**Sources**: [modules/ffmpegApi.py272-405](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L272-L405) [README.md103](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/README.md?plain=1#L103-L103)

## 横竖屏转换

```python
    # 横竖转换Filter
    def rotate_filter(self, image_, scale_x='1080', scale_y='1920', input=None):
            if image_[0] == 'H2V-I':
                # ffmpeg 命令：横屏转竖屏，视频宽边保持，图片缩放，视频下方叠加图片，空白区域显示为透明
                if input != 'flag':
                    duration = self.get_duration(input)
                else:
                    duration = '@duration'
                filter = f'-filter_complex "[1:v]scale={scale_x}:{scale_y},setsar=1,loop=-1:size={duration}[bg];[0:v]scale={scale_x}:-2,setsar=1[v];[bg][v]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]" -map "[vout]" -map 0:a'
                filter = f'-filter_complex "[1:v]scale={scale_x}:{scale_y},setsar=1,loop=-1:size={duration}[bg];[0:v]scale={scale_x}:-2,setsar=1[v];[bg][v]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]" -map "[vout]" -map 0:a'
            elif image_[0] == 'H2V-T':
                # ffmpeg 命令：横屏转竖屏，背景叠加模糊视频
                filter = f'-filter_complex "[0:v]split=2[v_main][v_bg];[v_main]scale=w={scale_x}:h=-1,setsar=1,pad={scale_x}:{scale_y}:(ow-iw)/2:(oh-ih)/2:color=black@0[v_scaled];[v_bg]crop=ih*{float(scale_x)/float(scale_y)}:ih,boxblur=10:5,scale={scale_x}:{scale_y}[bg_blurred];[bg_blurred][v_scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]" -map "[vout]" -map 0:a'
            elif image_[0] == 'H2V-B':
                # ffmpeg 命令：横屏转竖屏，不叠加图片，空白区域显示为黑色
                filter = f'-filter_complex "[0:v]scale=w={scale_x}:h=-1,setsar=1,pad={scale_x}:{scale_y}:(ow-iw)/2:(oh-ih)/2:black[vout]" -map "[vout]" -map 0:a'
            elif image_[0] == 'V2H-I':
                # ffmpeg 命令：竖屏转横屏，视频宽边保持，图片缩放，视频下方叠加图片，空白区域显示为透明
                if input != 'flag':
                    duration = self.get_duration(input)
                else:
                    duration = '@duration'
                filter = f'-filter_complex "[1:v]scale={scale_x}:{scale_y},setsar=1,loop=-1:size={duration}[bg];[0:v]scale=-2:{scale_y},setsar=1[v];[bg][v]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]" -map "[vout]" -map 0:a'
            elif image_[0] == 'V2H-T':
                # ffmpeg 命令：竖屏转横屏，背景叠加模糊视频
                filter = f'-filter_complex "[0:v]split=2[v_main][v_bg];[v_main]scale=w=-1:h={scale_y},setsar=1,pad={scale_x}:{scale_y}:(ow-iw)/2:(oh-ih)/2:color=black@0[v_scaled];[v_bg]crop=iw:iw*{float(scale_y)/float(scale_x)},boxblur=10:5,scale={scale_x}:{scale_y}[bg_blurred];[bg_blurred][v_scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[vout]" -map "[vout]" -map 0:a'
            elif image_[0] == 'V2H-B':
                # ffmpeg 命令：竖屏转横屏，不叠加图片，空白区域显示为黑色
                filter = f'-filter_complex "[0:v]scale=-1:h={scale_y},setsar=1,pad={scale_x}:{scale_y}:(ow-iw)/2:(oh-ih)/2:black[vout]" -map "[vout]" -map 0:a'
            else:
                return
            return filter
```

# Video Extraction and Cutting

<details style="box-sizing: border-box; border-width: 1px; border-style: solid; border-color: rgb(224, 224, 224); border-image: none 100% / 1 / 0 stretch; margin: 0px 0px 0.5rem; padding: 0.5rem 0.75rem; outline-color: oklab(0.708 0 0 / 0.5); border-radius: 0.5rem; color: rgb(51, 51, 51); font-family: Geist, &quot;Geist Fallback&quot;; font-size: 14.8px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(248, 247, 246); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;"><summary style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: -0.5rem; padding: 0.5rem; outline-color: oklab(0.708 0 0 / 0.5); display: flex; cursor: pointer; align-items: center; gap: 0.5rem; list-style: none;">Relevant source files</summary><ul style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 1.15em 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); list-style: disc; padding-inline-start: 1.45em;"><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>docs/DETAIL20240513.md</span></a></li><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/UpdateLog-version-pre0.1-pre2.0.md?plain=1" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>docs/UpdateLog-version-pre0.1-pre2.0.md</span></a></li><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>modules/ffmpegApi.py</span></a></li><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>modules/vcodecp_Interface.py</span></a></li></ul></details>

## Purpose and Scope

This document details the video extraction and cutting functionality in VideoExtractAndConcat. These operations allow users to remove unwanted portions from video files by specifying time parameters. The system supports two distinct modes:

- **Extraction Mode**: Removes opening and ending credits by specifying durations to trim from the start and end
- **Cutting Mode**: Extracts a specific time range by specifying start and end timestamps

For information about merging extracted segments, see [5.2](https://deepwiki.com/wish2333/VidExtConcat/5.2-video-merging-and-concatenation). For encoding options that apply during extraction/cutting, see [5.3](https://deepwiki.com/wish2333/VidExtConcat/5.3-video-and-audio-encoding).

------

## Operation Modes

The system provides two conceptually different approaches to removing video segments, implemented through separate FFmpeg command patterns.

```

```

**Sources**: modules/ffmpegApi.py, modules/vcodecp_Interface.py, docs/DETAIL20240513.md

------

## Core Components

The extraction and cutting system consists of three primary layers that work together to process video segments.

| Component          | File Location                | Key Classes/Functions                                 | Responsibility                         |
| ------------------ | ---------------------------- | ----------------------------------------------------- | -------------------------------------- |
| **UI Layer**       | modules/vcodecp_Interface.py | `VcodecpInterface`, `extract_or_cut_video()`          | User input, validation, mode selection |
| **Business Logic** | modules/vcodecp_Interface.py | `Worker.extract_video()`, `Worker.cut_video()`        | Task wrapping, threading               |
| **FFmpeg API**     | modules/ffmpegApi.py         | `FFmpeg.extract_video_single()`, `FFmpeg.cut_video()` | Command construction, execution        |

### Class Hierarchy and Method Dispatch

```

```

**Sources**: modules/vcodecp_Interface.py:425-461, modules/ffmpegApi.py:191-241

------

## Time Format Handling

The system uses a custom time format that differs from FFmpeg's native format, requiring conversion at the API boundary.

### Format Specification

| Source            | Format Pattern | Example        | Notes                            |
| ----------------- | -------------- | -------------- | -------------------------------- |
| **UI Input**      | `H:mm:ss:fff`  | `0:01:30:500`  | Milliseconds separated by colon  |
| **FFmpeg Format** | `HH:MM:SS.mmm` | `00:01:30.500` | Milliseconds after decimal point |

### Time Conversion Implementation

The conversion from UI format to FFmpeg format occurs at [modules/ffmpegApi.py199-228](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L199-L228):

```
# Conversion pattern: replace 8th character (colon) with period
start_time = start_time[:7] + '.' + start_time[8:]
# Input:  "0:01:30:500"
# Output: "0:01:30.500"
```

### Duration-Based End Time Calculation

Extraction mode requires calculating the actual end timestamp by subtracting the ending duration from total video duration. The `time_calculate()` method implements this logic:

```

```

Implementation details at [modules/ffmpegApi.py135-150](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L135-L150):

| Step                | Code                                                         | Purpose                      |
| ------------------- | ------------------------------------------------------------ | ---------------------------- |
| Parse time string   | `hours, minutes, seconds, milliseconds = end.split(':')`     | Split by colon separator     |
| Convert to seconds  | `end_float = hours*3600 + minutes*60 + float(seconds) + float(milliseconds)/1000` | Total seconds as float       |
| Calculate end point | `end_time_float = duration - end_float`                      | Subtract from total duration |
| Format output       | `"%02d:%02d:%06.3f" % (h, m, s)`                             | FFmpeg-compatible format     |

**Sources**: modules/ffmpegApi.py:135-150, 199, 228-229, docs/DETAIL20240513.md:249-268

------

## Extraction Operations

Extraction mode removes opening and ending credits by calculating the appropriate end timestamp based on video duration.

### extract_video_single() Workflow

```

```

### FFmpeg Command Construction

The extraction command is built at [modules/ffmpegApi.py205-213](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L205-L213):

```
cmd = [
    '-hide_banner',      # Suppress FFmpeg version banner
    overwrite,           # '-y' to overwrite existing files
    '-ss', start_time,   # Seek to start position (converted format)
    '-to', end_time,     # Calculated end timestamp
    '-accurate_seek',    # Enable accurate seeking (slower but precise)
    '-i', f'"{input_file}"',  # Input file path (quoted for spaces)
    encoder,             # Encoding parameters (e.g., '-c:v copy -c:a copy')
    f'"{output_file}"'   # Output file path
]
```

### Accurate Seeking Trade-offs

The `-accurate_seek` flag is critical for batch processing, as documented at [docs/DETAIL20240513.md270](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1#L270-L270):

> FFmpeg命令中，核心在于传入-accurate_seek参数，虽然不能精准定位，从而导致切不到真正想要的时间点和片段，但是胜在不出错，对于批量处理这种粗糙工作来说是更好的选择

**Translation**: Accurate seek doesn't achieve frame-perfect precision but prioritizes reliability over accuracy, which is preferable for batch operations.

**Sources**: modules/ffmpegApi.py:191-218, docs/DETAIL20240513.md:233-330

------

## Cutting Operations

Cutting mode extracts a specific time range using explicit start and end timestamps without duration calculations.

### cut_video() Implementation

The cutting operation is simpler than extraction because it uses direct timestamps:

```

```

### Command Structure Comparison

| Aspect              | Extraction Mode                         | Cutting Mode                |
| ------------------- | --------------------------------------- | --------------------------- |
| **Method**          | `extract_video_single()`                | `cut_video()`               |
| **End Time Source** | Calculated from duration                | User-provided timestamp     |
| **Prerequisites**   | Requires FFprobe call                   | No external calls needed    |
| **Use Case**        | Remove opening/ending of known duration | Extract specific time range |
| **Command Pattern** | `-ss START -to CALCULATED_END`          | `-ss START -to END`         |

Implementation at [modules/ffmpegApi.py220-241](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L220-L241):

```
def cut_video(self, input_file, output_file, start_time, end_time, 
              encoder='-c:v copy -c:a copy', overwrite='-y'):
    # Format conversion for both timestamps
    start_time = start_time[:7] + '.' + start_time[8:]
    end_time = end_time[:7] + '.' + end_time[8:]
    
    cmd = [
        '-hide_banner',
        overwrite, 
        '-ss', start_time,   # Direct start timestamp
        '-to', end_time,     # Direct end timestamp
        '-accurate_seek', 
        '-i', f'"{input_file}"',  
        encoder, 
        f'"{output_file}"'
    ]
    self.run(cmd)
```

**Sources**: modules/ffmpegApi.py:220-241, docs/DETAIL20240513.md:207-231

------

## UI Integration and Workflow

The extraction/cutting interface provides radio button mode selection and time input widgets.

### UI State Management

```

```

### Event Binding and Validation

The UI layer implements validation at [modules/vcodecp_Interface.py417-461](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L417-L461):

| UI Element          | Object Name                 | Purpose                           | Lines   |
| ------------------- | --------------------------- | --------------------------------- | ------- |
| **Enable Checkbox** | `VcodecpIFcheckBox_extract` | Toggle extraction/cutting mode    | 417-423 |
| **Time Input 1**    | `VcodecpIFtimeEdit_3`       | Start time or opening duration    | 419     |
| **Time Input 2**    | `VcodecpIFtimeEdit_2`       | End time or ending duration       | 420     |
| **Mode Radio 1**    | `VcodecpIFradioButton`      | Select extraction mode (片尾时长) | 431     |
| **Mode Radio 2**    | `VcodecpIFradioButton_2`    | Select cutting mode (结束时间)    | 445     |

### Execution Flow with Threading

```

```

### Validation Rules

The system enforces several validation constraints at [modules/vcodecp_Interface.py613-637](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L613-L637):

| Rule                   | Check                                           | Error Message            | Code Location |
| ---------------------- | ----------------------------------------------- | ------------------------ | ------------- |
| **Mutual Exclusivity** | Cannot enable extraction + acceleration + merge | "请勿同时选择滤镜选项！" | 614-630       |
| **Non-zero Times**     | Times must not be 0:00:00:000                   | "切割时长不能为零！"     | 633-635       |
| **File Existence**     | Input file must exist                           | "不存在！"               | 458-460       |

**Sources**: modules/vcodecp_Interface.py:417-461, 613-637

------

## Batch Processing Support

While the primary interface (`VcodecpInterface`) focuses on single-file operations, the FFmpeg API provides folder-based batch extraction.

### extract_video() Method

The folder-based extraction method at [modules/ffmpegApi.py152-188](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L152-L188) iterates through MP4 files:

```
def extract_video(self, input_folder, start_time, end, output_folder, 
                  encoder='-c:v copy -c:a copy', overwrite='-y'):
    # Iterate through all mp4 files in folder
    for file in os.listdir(input_folder):
        if file.endswith('.mp4'):
            input_file = os.path.join(input_folder, file)
            
            # Create output folder if needed
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            output_file = os.path.join(output_folder, file)
            
            # Get duration and calculate end time
            duration = self.get_duration(input_file)
            end_time = self.time_calculate(duration, end)
            
            # Execute extraction
            cmd = ['-hide_banner', overwrite, '-ss', start_time, 
                   '-to', end_time, '-accurate_seek', 
                   '-i', f'"{input_file}"', encoder, f'"{output_file}"']
            self.run(cmd)
```

### Folder vs Single-File Operations

| Operation        | Method                   | Input Type  | Use Case                                 |
| ---------------- | ------------------------ | ----------- | ---------------------------------------- |
| **Batch Folder** | `extract_video()`        | Folder path | Process all MP4 files in folder          |
| **Single File**  | `extract_video_single()` | File path   | Process one specific file                |
| **Cutting**      | `cut_video()`            | File path   | Time-range extraction (single file only) |

**Note**: The folder-based method is defined but not currently exposed through the UI layer. The interface at [modules/vcodecp_Interface.py425-461](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L425-L461) only calls single-file operations.

**Sources**: modules/ffmpegApi.py:152-188, modules/vcodecp_Interface.py:425-461

------

## Duration Retrieval with FFprobe

Video duration is obtained using FFprobe with a specialized command pattern.

### get_duration() Implementation

```

```

Implementation at [modules/ffmpegApi.py111-132](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L111-L132):

```
def get_duration(self, input_file):
    cmd1 = [
        self.ffprobe_path, 
        '-v', 'error',                    # Suppress warnings
        '-show_entries', 'format=duration',  # Request duration only
        '-of', 'default=noprint_wrappers=1:nokey=1',  # Plain output
        input_file
    ]
    
    result = subprocess.run(cmd1, capture_output=True, text=True)
    stdout = result.stdout.strip()
    
    if not stdout:
        logger.error("ffprobe 输出为空，无法获取视频持续时间")
        return None
    
    try:
        duration = float(stdout)
        logger.debug("视频总秒数为：" + str(duration))
        return duration
    except ValueError as e:
        logger.error("转换视频持续时间为浮点数时出错：", str(e))
        raise e
```

### Command Output Format

| FFprobe Flag                             | Purpose                  | Effect                                |
| ---------------------------------------- | ------------------------ | ------------------------------------- |
| `-v error`                               | Suppress verbose output  | Only show errors                      |
| `-show_entries format=duration`          | Select specific metadata | Return only duration field            |
| `-of default=noprint_wrappers=1:nokey=1` | Format output            | Return raw float value without labels |

**Example output**: `125.482000` (seconds)

**Sources**: modules/ffmpegApi.py:111-132, docs/DETAIL20240513.md:282-286

------

## Error Handling and Interruption

The extraction/cutting operations support graceful interruption through the multi-threaded architecture described in [3.2](https://deepwiki.com/wish2333/VidExtConcat/3.2-multi-threading-and-asynchronous-execution).

### Interrupt Mechanism

When a user clicks the stop button during processing:

```

```

Implementation at [modules/vcodecp_Interface.py772-783](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L772-L783):

| Step                | Code                                               | Purpose                             |
| ------------------- | -------------------------------------------------- | ----------------------------------- |
| Check worker state  | `if self.worker._started_flag:`                    | Verify task is running              |
| Set interrupt flag  | `self.worker.interrupt()`                          | Signal interrupt to FFmpeg instance |
| Update FFmpeg flag  | `self.ffmpeg_instance.update_interrupt_flag(True)` | Set instance interrupt flag         |
| Guardian detection  | Guardian thread checks flag every second           | Monitor for interruption            |
| Process termination | `self.p.terminate()` then `self.p.kill()`          | Gracefully stop FFmpeg              |

**Sources**: modules/vcodecp_Interface.py:772-783, modules/ffmpegApi.py:26-46

------

## Summary

The video extraction and cutting system provides two operational modes through a unified interface:

1. **Extraction Mode**: Calculates end timestamps from video duration to remove opening/ending credits
2. **Cutting Mode**: Uses explicit time ranges for segment extraction

Both modes utilize the same underlying FFmpeg execution infrastructure with `-accurate_seek` for reliable batch processing, time format conversion for UI/FFmpeg compatibility, and multi-threaded execution with interrupt support for UI responsiveness.

**Sources**: modules/vcodecp_Interface.py, modules/ffmpegApi.py, docs/DETAIL20240513.md

# Video Merging and Concatenation

<details style="box-sizing: border-box; border-width: 1px; border-style: solid; border-color: rgb(224, 224, 224); border-image: none 100% / 1 / 0 stretch; margin: 0px 0px 0.5rem; padding: 0.5rem 0.75rem; outline-color: oklab(0.708 0 0 / 0.5); border-radius: 0.5rem; color: rgb(51, 51, 51); font-family: Geist, &quot;Geist Fallback&quot;; font-size: 14.8px; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; background-color: rgb(248, 247, 246); text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;"><summary style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: -0.5rem; padding: 0.5rem; outline-color: oklab(0.708 0 0 / 0.5); display: flex; cursor: pointer; align-items: center; gap: 0.5rem; list-style: none;">Relevant source files</summary><ul style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 1.15em 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); list-style: disc; padding-inline-start: 1.45em;"><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>docs/DETAIL20240513.md</span></a></li><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/UpdateLog-version-pre0.1-pre2.0.md?plain=1" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>docs/UpdateLog-version-pre0.1-pre2.0.md</span></a></li><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>modules/ffmpegApi.py</span></a></li><li style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0.35em 0px; padding: 0px 0px 0px 1.5rem; outline-color: oklab(0.708 0 0 / 0.5); list-style: none; padding-inline-start: 0.45em;"><a href="https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py" target="_blank" rel="noopener noreferrer" class="mb-1 mr-1 inline-flex items-stretch font-mono text-xs !no-underline transition-opacity hover:opacity-75" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px 4px 4px 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); color: rgb(51, 51, 51); text-decoration: underline; font-weight: 500; display: inline-flex; align-items: stretch; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, &quot;Liberation Mono&quot;, &quot;Courier New&quot;, monospace; font-size: 12px; line-height: 1.33333; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 0.15s;"><span class="flex items-center break-all rounded-l px-2 py-1.5 bg-[#e5e5e5] text-[#333333] dark:bg-[#252525] dark:text-[#e4e4e4] rounded-r" style="box-sizing: border-box; border: 0px solid oklch(0.922 0 0); margin: 0px; padding: 0px; outline-color: oklab(0.708 0 0 / 0.5); display: flex; align-items: center; border-radius: 0.25rem; background-color: rgb(229, 229, 229); padding-inline: 8px; padding-block: 6px; word-break: break-all; color: rgb(51, 51, 51);"><svg class="mr-1.5 hidden h-3.5 w-3.5 flex-shrink-0 opacity-40 md:block" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path></svg>modules/vcodecp_Interface.py</span></a></li></ul></details>

## Purpose and Scope

This document describes the video merging and concatenation functionality in VideoExtractAndConcat, which allows users to combine multiple video files into a single output with automatic normalization of video properties. The system supports merging 2 or 3 video files, with common use cases including adding opening (OP) and ending (ED) sequences to main content videos.

For information about video cutting and extraction operations, see [Video Extraction and Cutting](https://deepwiki.com/wish2333/VidExtConcat/5.1-video-extraction-and-cutting). For encoding-only operations without merging, see [Video and Audio Encoding](https://deepwiki.com/wish2333/VidExtConcat/5.3-video-and-audio-encoding).

## Merge Operation Types

The application provides three distinct merge operations, each designed for different use cases:

| Operation          | Method                 | Files                  | Description                                    | Use Case                            |
| ------------------ | ---------------------- | ---------------------- | ---------------------------------------------- | ----------------------------------- |
| 3-file merge       | `merge_video()`        | OP + Main + ED         | Concatenates opening, main content, and ending | Episode processing with intro/outro |
| 2-file merge       | `merge_video_two()`    | OP + Main OR Main + ED | Concatenates two files in sequence             | Partial episode processing          |
| Folder batch merge | `merge_video_folder()` | OP + Folder + ED       | Batch processes all videos in folder           | Bulk episode processing             |

**Sources:** [modules/ffmpegApi.py244-322](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L244-L322) [docs/DETAIL20240513.md332-424](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1#L332-L424)

## Merge Operation Architecture

```

```

**Sources:** [modules/vcodecp_Interface.py463-609](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L463-L609) [modules/vcodecp_Interface.py75-83](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L75-L83) [modules/ffmpegApi.py272-322](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L272-L322)

## Video Normalization with filter_complex

The merging operations use FFmpeg's `-filter_complex` parameter to normalize video properties before concatenation. This is essential for preventing errors when merging videos with different characteristics.

### Normalized Properties

The system normalizes five critical video properties:

1. **Frame Rate (fps)**: All inputs standardized to target fps (default: 30)
2. **Resolution (scale)**: All inputs resized to target resolution (default: 1920:1080)
3. **Aspect Ratio (setsar)**: Pixel aspect ratio set to 1:1 (square pixels)
4. **Audio Sample Rate**: Standardized to 44100 Hz
5. **Audio Channels**: Converted to stereo (2 channels)

### Filter Pipeline for 3-File Merge

```

```

**Sources:** [modules/ffmpegApi.py282-295](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L282-L295) [docs/DETAIL20240513.md334-368](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1#L334-L368)

## Three-File Merge Operation

The `merge_video()` function concatenates three files: opening, main content, and ending. This is the most common workflow for episodic content processing.

### Method Signature

The function accepts the following parameters:

| Parameter     | Type | Default                                                      | Description                         |
| ------------- | ---- | ------------------------------------------------------------ | ----------------------------------- |
| `input_file`  | str  | required                                                     | Path to main content file           |
| `output_file` | str  | required                                                     | Path to output file                 |
| `input_file1` | str  | required                                                     | Path to OP file (opening)           |
| `input_file2` | str  | required                                                     | Path to ED file (ending)            |
| `encoder`     | str  | `-c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k -ar 44100 -ac 2` | Encoding parameters                 |
| `resolution`  | str  | `1920:1080`                                                  | Target resolution (colon-separated) |
| `fps`         | str  | `30`                                                         | Target frame rate                   |
| `overwrite`   | str  | `-y`                                                         | Overwrite existing output           |

### FFmpeg Command Structure

The generated FFmpeg command follows this pattern:

```
ffmpeg -hide_banner -y 
  -i "input_file1"  # OP file
  -i "input_file"   # Main content
  -i "input_file2"  # ED file
  -filter_complex "[0:v]fps=30,scale=1920:1080,setsar=1[v0];
                   [1:v]fps=30,scale=1920:1080,setsar=1[v1];
                   [2:v]fps=30,scale=1920:1080,setsar=1[v2];
                   [0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];
                   [1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1];
                   [2:a]aformat=sample_rates=44100:channel_layouts=stereo[a2];
                   [v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[vout][aout]"
  -map "[vout]" -map "[aout]"
  -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k 
  "output_file"
```

**Sources:** [modules/ffmpegApi.py272-297](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L272-L297) [docs/DETAIL20240513.md374-399](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1#L374-L399)

## Two-File Merge Operation

The `merge_video_two()` function concatenates two files. This is used when only OP or ED is available, or for simpler merge scenarios.

### Method Signature

| Parameter     | Type | Default                                                      | Description                         |
| ------------- | ---- | ------------------------------------------------------------ | ----------------------------------- |
| `op_file`     | str  | required                                                     | First file in sequence              |
| `output_file` | str  | required                                                     | Path to output file                 |
| `ed_file`     | str  | required                                                     | Second file in sequence             |
| `encoder`     | str  | `-c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k -ar 44100 -ac 2` | Encoding parameters                 |
| `resolution`  | str  | `1920:1080`                                                  | Target resolution (colon-separated) |
| `fps`         | str  | `30`                                                         | Target frame rate                   |
| `overwrite`   | str  | `-y`                                                         | Overwrite existing output           |

### Filter Pipeline for 2-File Merge

The filter_complex differs from 3-file merge only in the concatenation count:

```
[0:v]fps=30,scale=1920:1080,setsar=1[v0];
[1:v]fps=30,scale=1920:1080,setsar=1[v1];
[0:a]aformat=sample_rates=44100:channel_layouts=stereo[a0];
[1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1];
[v0][a0][v1][a1]concat=n=2:v=1:a=1[vout][aout]
```

Note the `concat=n=2` parameter indicating 2 input file segments.

**Sources:** [modules/ffmpegApi.py299-322](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L299-L322) [docs/DETAIL20240513.md401-423](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1#L401-L423)

## Batch Folder Merging

The `merge_video_folder()` function processes all `.mp4` files in a folder, merging each with specified OP and ED files.

### Operation Flow

```

```

The method iterates through all files in the input folder, applying the same OP and ED files to each main content video.

**Sources:** [modules/ffmpegApi.py244-270](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/ffmpegApi.py#L244-L270) [docs/DETAIL20240513.md337-368](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/docs/DETAIL20240513.md?plain=1#L337-L368)

## UI Workflow for Merge Operations

### Enable Merge Mode

The batch processing interface provides merge functionality through the following UI flow:

```

```

**Sources:** [modules/vcodecp_Interface.py492-609](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L492-L609)

### Decision Logic for Merge Type

The `merge_or_concat_video()` method determines which merge operation to execute based on user selections:

```

```

**Sources:** [modules/vcodecp_Interface.py463-491](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L463-L491)

## Resolution and FPS Configuration

### UI Configuration Flow

Users can optionally override default resolution and fps values through checkboxes:

| UI Element            | Property          | Default   | Action                                 |
| --------------------- | ----------------- | --------- | -------------------------------------- |
| `VcodecpIFcheckBox_2` | Enable Resolution | Unchecked | Enables `VcodecpIFlineEdit` combobox   |
| `VcodecpIFlineEdit`   | Resolution        | 1920x1080 | Selected from predefined list          |
| `VcodecpIFcheckBox_3` | Enable FPS        | Unchecked | Enables `VcodecpIFlineEdit_2` combobox |
| `VcodecpIFlineEdit_2` | FPS               | 30        | Selected from predefined list          |

### Resolution Format Conversion

The UI uses `x` as separator (e.g., `1920x1080`), but FFmpeg requires `:` separator (e.g., `1920:1080`). The conversion happens in merge methods:

```
# In merge_3_videos() and merge_2_videos()
if self.VcodecpIFcheckBox_2.isChecked():
    resolution = self.VcodecpIFlineEdit.text().replace('x', ':')
else:
    resolution = '1920:1080'  # Default
```

**Sources:** [modules/vcodecp_Interface.py505-608](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L505-L608) [modules/vcodecp_Interface.py138-147](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L138-L147)

## Worker Thread Execution

### Task Dispatching

The merge operations execute in separate threads to prevent UI blocking:

```

```

**Sources:** [modules/vcodecp_Interface.py75-83](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L75-L83) [modules/vcodecp_Interface.py505-608](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L505-L608)

### Signal Connections

The merge operations connect the following signals for progress tracking:

```
self.thread.started.connect(
    lambda: self.VcodecpIFconsole.appendPlainText(f"{self.merge_input_file}开始视频合并")
)
self.thread.finished.connect(
    lambda: self.VcodecpIFconsole.appendPlainText(f"{self.merge_input_file}完成视频合并")
)
self.thread.finished.connect(self.worker.deleteLater)
self.thread.finished.connect(self.thread.deleteLater)
self.thread.finished.connect(self.on_thread_finished)  # Process next file
```

**Sources:** [modules/vcodecp_Interface.py521-530](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L521-L530) [modules/vcodecp_Interface.py559-601](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L559-L601)

## Parameter Resolution Logic

The `merge_3_videos()` and `merge_2_videos()` methods implement conditional parameter passing based on UI state:

### Parameter Matrix

| Resolution Checked | FPS Checked | Parameters Passed to Worker                 |
| ------------------ | ----------- | ------------------------------------------- |
| No                 | No          | `resolution='1920:1080', fps=30` (defaults) |
| Yes                | No          | `resolution=user_value` (from UI)           |
| No                 | Yes         | `resolution='1920:1080', fps=user_value`    |
| Yes                | Yes         | `resolution=user_value, fps=user_value`     |

### Implementation Example

```
if self.VcodecpIFcheckBox_2.isChecked() and self.VcodecpIFcheckBox_3.isChecked():
    resolution = self.VcodecpIFlineEdit.text().replace('x', ':')
    self.worker = Worker('merge_video', ..., resolution, self.VcodecpIFlineEdit_2.text())
elif self.VcodecpIFcheckBox_2.isChecked() and not self.VcodecpIFcheckBox_3.isChecked():
    resolution = self.VcodecpIFlineEdit.text().replace('x', ':')
    self.worker = Worker('merge_video', ..., resolution)
elif not self.VcodecpIFcheckBox_2.isChecked() and self.VcodecpIFcheckBox_3.isChecked():
    resolution = '1920:1080'
    self.worker = Worker('merge_video', ..., resolution, self.VcodecpIFlineEdit_2.text())
else:
    resolution = '1920:1080'
    fps = 30
    self.worker = Worker('merge_video', ..., resolution, fps)
```

**Sources:** [modules/vcodecp_Interface.py508-520](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L508-L520) [modules/vcodecp_Interface.py546-591](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L546-L591)

## Error Handling

### File Validation

The merge methods validate file existence before execution:

```
if os.path.isfile(self.merge_input_file) and os.path.isfile(self.op_file) and os.path.isfile(self.ed_file):
    # Execute merge
else:
    if not os.path.isfile(self.merge_input_file):
        MessageBox("input错误", f"{self.merge_input_file}不存在！", parent=self).exec()
    elif not os.path.isfile(self.op_file):
        MessageBox("op错误", f"{self.op_file}不存在！", parent=self).exec()
    elif not os.path.isfile(self.ed_file):
        MessageBox("ed错误", f"{self.ed_file}不存在！", parent=self).exec()
```

### Conflict Detection

The UI prevents conflicting operations through the `debug_of_filter_config()` method:

- Merge cannot be combined with acceleration (`VcodecpIFcheckBox_4`)
- Merge cannot be combined with extraction (`VcodecpIFcheckBox_extract`)
- Displays warning MessageBox if conflicts detected

**Sources:** [modules/vcodecp_Interface.py531-541](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L531-L541) [modules/vcodecp_Interface.py613-637](https://github.com/wish2333/VidExtConcat/blob/9a1d9329/modules/vcodecp_Interface.py#L613-L637)

## Batch Processing Loop

For batch operations with multiple input files, the merge logic integrates with the main processing loop:

```
def encoding(self):
    # ... validation ...
    if self.input_file_args != [] and self.output_file_args != []:
        while self.i < len(self.input_file_args):
            if self.is_paused:
                break
            self.simple_encoding()      # Skip if merge enabled
            self.accelerated_encoding() # Skip if merge enabled
            self.extract_or_cut_video() # Skip if merge enabled
            self.merge_or_concat_video() # Execute merge
        else:
            self.i = 0  # Reset counter
```

The `on_thread_finished()` callback advances the loop index and recursively calls `encoding()` to process the next file.

# 基础视频剪辑拼接

除了上述特殊场景的剪辑拼接以外，还需要实现常规的多文件拼接（三种方式可选，详见FFmpeg官网推荐两种快速拼接+上述filtercomplex重编码拼接）