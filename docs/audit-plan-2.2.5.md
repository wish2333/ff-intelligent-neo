# Plan: Fix Subtitle Handling in Audio/Video Mix

## Context

The project's "Audio/Subtitle Mix" (音视频混流) feature has a broken subtitle implementation:

1. **Hardcoded map index bug**: `-map 2:s` always assumes subtitle is input #2, but when there's no external audio, subtitle is input #1, causing `Invalid input file index: 2`
2. **Only supports soft embedding**: The current code only embeds subtitles as a soft stream (`-c:s mov_text`), which doesn't work for ASS subtitles with effects. Users need **burn/hardcode** mode using the `subtitles` or `ass` video filter.
3. **No subtitle mode selector**: The UI has no way to choose between embed (soft) and burn (hardcode) modes.

## Approach

Add a `subtitle_mode` field (`"embed"` | `"burn"`) to `AudioSubtitleConfig`. When `burn`, use the `subtitles` video filter to hardcode subtitles into the video. When `embed` (default), fix the map index calculation for soft embedding.

## Files to Modify

### 1. `core/models.py` - AudioSubtitleConfig dataclass (~line 226)

- Add field: `subtitle_mode: str = "embed"` (values: `"embed"` or `"burn"`)
- Update `to_dict()` and `from_dict()` with backward-compatible default

### 2. `core/command_builder.py` - Command building (two locations)

**`build_command()` ~line 1090-1115** (main execution path):

- When `subtitle_mode == "burn"`: DON'T add subtitle as `-i` input. Instead, inject `subtitles=<escaped_path>` into the video filter chain. The path must escape `\` to `/` and `:` to `\:` for FFmpeg filter syntax.
- When `subtitle_mode == "embed"`: Fix map index to be dynamic based on input count instead of hardcoded `2:s`.

**`build_avsmix_command()` ~line 828-832** (dedicated avsmix builder):

- Same logic: burn mode uses video filter, embed mode fixes map index.

**Burn mode path escaping helper** (new utility near `_subprocess_quote`):

```python
def _ffmpeg_filter_escape_path(path: str) -> str:
    """Escape path for FFmpeg filter value (subtitles=...)."""
    # Convert backslashes to forward slashes
    p = path.replace("\\", "/")
    # Escape colons for filter parser
    p = p.replace(":", "\\:")
    return p
```

### 3. `frontend/src/types/config.ts` - TypeScript type (~line 54)

- Add `subtitle_mode: string` to `AudioSubtitleConfigDTO`

### 4. `frontend/src/composables/useGlobalConfig.ts` (~line 69)

- Add `subtitle_mode: "embed"` to `DEFAULT_AVSMIX`

### 5. `frontend/src/pages/AudioSubtitlePage.vue` - UI

- Add subtitle mode selector (radio buttons or toggle) below the subtitle file drop zone, visible when `subtitle_path` is set
- When mode is "burn", hide the language code field (not applicable)
- When mode is "embed", show language code field as before

### 6. `frontend/src/i18n/locales/zh-CN.ts` and `en.ts`

- Add i18n keys for the subtitle mode selector:
  - `avMix.subtitle.mode`: "Subtitle Mode" / "字幕模式"
  - `avMix.subtitle.modeEmbed`: "Embed (Soft Subtitle)" / "嵌入 (软字幕)"
  - `avMix.subtitle.modeBurn`: "Burn (Hardcode)" / "压制 (内嵌字幕)"
  - `avMix.subtitle.modeBurnHint`: "Burns subtitle effects into video, requires re-encoding" / "将特效字幕烧录到画面中，需要重新编码"

### 7. `docs/fields/AudioSubtitleConfig.csv`

- Add `subtitle_mode` field definition

## Burn Mode Command Logic (Key Detail)

For burn mode, the generated FFmpeg command should be:

```
ffmpeg -i input.mp4 -vf "subtitles='Q\:/path/to/sub.ass'" -c:v av1_nvenc -cq 32 -c:a copy output.mp4
```

NOT:

```
ffmpeg -i input.mp4 -i sub.ass -map 2:s -c:s mov_text output.mp4  # WRONG (current)
```

When burn mode is combined with other video filters (crop, rotate, etc.), the `subtitles` filter is appended to the existing vf_segments chain. When combined with external audio, the subtitle goes through `-vf` while the audio uses `-map`.

## Embed Mode Fix (Map Index)

Current (broken):

```python
map_directives.extend(["-map", "2:s", "-c:s", "mov_text"])
```

Fixed: calculate index dynamically:

```python
# Count inputs: 0=video, then extra_inputs, then avsmix_inputs
subtitle_input_idx = 1  # after video input #0
if avsmix.external_audio_path:
    subtitle_input_idx += 1
map_directives.extend(["-map", f"{subtitle_input_idx}:s", "-c:s", "mov_text"])
```

## Verification

1. Run `uv run pytest test/` to ensure existing tests pass
2. Start the app with `uv run dev.py` and test:
   - Subtitle only (no external audio) with "embed" mode - should work
   - Subtitle only with "burn" mode - should generate correct `subtitles=` filter
   - External audio + subtitle with "embed" mode - map index should be 2
   - External audio + subtitle with "burn" mode - audio via map, subtitle via filter
3. Verify command preview shows correct FFmpeg command