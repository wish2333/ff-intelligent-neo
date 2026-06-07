# Audit Report v2.2.4 - Audio/Video Muxing & Config Combination Logic

- Date: 2026-05-25
- Scope: Frontend useGlobalConfig, AudioSubtitlePage, MergePage, CommandConfigPage; Backend command_builder, task_runner
- Severity Levels: CRITICAL / HIGH / MEDIUM / LOW

---

## Summary

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| 1 | merge + avsmix silent conflict, avsmix silently ignored | HIGH | command_builder.py:1020-1031 |
| 2 | loadFromTaskConfig activeMode sequential overwrite | HIGH | useGlobalConfig.ts:153-169 |
| 3 | task_runner merge priority prevents global intro/outro override | MEDIUM | task_runner.py:117-122 |
| 4 | loadFromTaskConfig does not reset activeMode before re-evaluation | MEDIUM | useGlobalConfig.ts:149-169 |
| 5 | MergePage bypasses toTaskConfig(), architecture inconsistency | LOW | MergePage.vue:94-101 |
| 6 | No merge+avsmix coexistence validation in validate_config | LOW | command_builder.py:1165-1294 |
| 7 | Config page "Merge" tab naming ambiguity | LOW | MergeSettingsForm.vue:1-8 |

---

## Issue #1: merge + avsmix silent conflict (HIGH)

### Description

`build_command` uses priority-based dispatch. The merge handler (intro/outro or multi-file concat) returns early **before** the avsmix code path is reached. If a TaskConfig contains both `merge` and `avsmix`, the avsmix settings are silently discarded with no warning to the user.

### Impact

User configures external audio/subtitle on AudioSubtitlePage, also sets global intro/outro on Config page. The resulting command silently drops the external audio and subtitle. No error, no warning.

### Code Path

1. `toTaskConfig()` in `useGlobalConfig.ts` includes both `merge` (if intro/outro set) and `avsmix` (if mode is avsmix) in the same TaskConfigDTO.
2. `build_command()` in `command_builder.py` dispatches to merge handler first, which returns before avsmix logic runs.

### Suggested Fix

Add a conflict check in `validate_config` that produces a warning when both `config.merge` and `config.avsmix` are active. Alternatively, add a frontend guard in `toTaskConfig()` that strips `avsmix` when `merge.intro_path` or `merge.outro_path` is set.

---

## Issue #2: loadFromTaskConfig activeMode sequential overwrite (HIGH)

### Description

`loadFromTaskConfig` checks `config.clip`, `config.merge`, `config.avsmix`, `config.custom_command` in sequence, each overwriting `activeMode`. If a config contains multiple sub-configs (e.g., clip + avsmix), only the **last** match determines the active mode.

### Impact

Loading a saved task that has both clip and avsmix settings will set `activeMode` to `"avsmix"`, losing awareness of the clip mode. The UI will show the avsmix page as active, but clip settings are also loaded -- creating a confusing state where the user sees avsmix but clip is silently active.

### Suggested Fix

Determine `activeMode` based on priority (custom > merge > avsmix > clip > transcode) rather than sequential overwrite.

---

## Issue #3: task_runner merge priority prevents global intro/outro (MEDIUM)

### Description

The task runner uses `current.merge or incoming.merge`, meaning the task-local merge config always wins. If a task was created from MergePage with its own merge config, then the user later sets global intro/outro on the Config page, the global intro/outro will NOT be applied to existing tasks.

### Impact

User expects "apply intro/outro to all tasks" behavior (as documented in MergeSettingsForm), but tasks created from MergePage are immune. This is by design (MergePage's local config is intentionally preserved) but creates a gap in the documented "all tasks" promise.

### Suggested Fix

Either:
- Document this exception clearly in the UI ("intro/outro applies to all tasks except merge tasks")
- Or change the merge strategy to: if incoming merge has intro/outro but current merge does not, apply incoming

---

## Issue #4: loadFromTaskConfig does not reset activeMode (MEDIUM)

### Description

`loadFromTaskConfig` only sets `activeMode` when a sub-config is found. If a loaded config has no clip/merge/avsmix/custom_command (e.g., transcode-only), `activeMode` retains whatever value it had before the load.

### Impact

User loads a transcode-only preset while in avsmix mode. The transcode settings are loaded correctly, but `activeMode` stays `"avsmix"`, so the next `toTaskConfig()` call still includes avsmix -- using stale avsmix settings that weren't part of the loaded preset.

### Suggested Fix

Reset `activeMode` to `"transcode"` at the start of `loadFromTaskConfig` before evaluating sub-configs.

---

## Issue #5: MergePage bypasses toTaskConfig() (LOW)

### Description

MergePage constructs its own TaskConfigDTO directly instead of using `toTaskConfig()`. This means any future changes to `toTaskConfig()` logic (e.g., adding a new cross-cutting concern) won't automatically apply to merge tasks.

### Impact

Maintainability concern. Currently intentional (to isolate merge config from global intro/outro), but creates a divergence pattern that could lead to bugs during future refactoring.

### Suggested Fix

Extract a shared helper like `buildBaseConfig(transcode, filters)` that both `toTaskConfig()` and MergePage use for the common parts.

---

## Issue #6: No merge+avsmix coexistence validation (LOW)

### Description

`validate_config` checks merge and avsmix independently but has no cross-check. There is no warning when both are active, even though the backend will silently ignore avsmix.

### Suggested Fix

Add validation rule:
```python
if config.merge and config.avsmix:
    if config.merge.intro_path or config.merge.outro_path or len(config.merge.file_list) >= 2:
        issues.append({
            "level": "warning",
            "param": "avsmix",
            "message": "Merge mode is active. Audio/subtitle settings will be ignored.",
        })
```

---

## Issue #7: Config page "Merge" tab naming ambiguity (LOW)

### Description

The Config page has a "Merge" tab (`MergeSettingsForm`) that only configures batch intro/outro. The actual multi-file merge lives on the separate MergePage. Users may expect the "Merge" tab to control all merge behavior.

### Suggested Fix

Rename the tab to "Intro/Outro" or add a subtitle explaining it only handles batch intro/outro wrapping.

---

## Appendix A: useGlobalConfig.ts - toTaskConfig() assembly logic

Source: `frontend/src/composables/useGlobalConfig.ts` lines 103-145

```typescript
export function useGlobalConfig() {
  const configRef = computed<TaskConfigDTO>(() => {
    const mode = activeMode.value
    // Always include transcode + filters as base
    const base: TaskConfigDTO = {
      transcode: { ...transcode },
      filters: { ...filters },
      output_dir: "",
    }
    // Custom command always overrides when raw_args is set, regardless of mode
    if (customCommand.raw_args.trim()) {
      base.custom_command = { ...customCommand }
    }
    // Global intro/outro: always include when set (applies to ALL queue tasks)
    if (merge.intro_path || merge.outro_path) {
      base.merge = { ...merge }
    }
    // Clip is an auxiliary config that layers onto transcode/filters.
    // Include it whenever data is filled, unless in merge or custom mode.
    if (clip.start_time || clip.end_time_or_duration) {
      if (mode !== "merge" && mode !== "custom") {
        base.clip = { ...clip }
      }
    }
    // Only include the mode-specific sub-config based on active mode
    if (mode === "merge") {
      // Only set merge if not already set by intro/outro above
      if (!base.merge) {
        base.merge = { ...merge }
      }
    } else if (mode === "avsmix") {
      base.avsmix = { ...avsmix }
    } else if (mode === "custom") {
      base.custom_command = { ...customCommand }
    }
    // mode === "transcode" / "filters" / "clip" -> transcode + filters + optional clip
    return base
  })
  // ...
}
```

Key observation: When `mode === "avsmix"` AND `merge.intro_path` is set, the returned TaskConfigDTO contains BOTH `merge` and `avsmix`. This triggers Issue #1.

---

## Appendix B: useGlobalConfig.ts - loadFromTaskConfig() sequential overwrite

Source: `frontend/src/composables/useGlobalConfig.ts` lines 149-169

```typescript
function loadFromTaskConfig(config: TaskConfigDTO) {
  // Use spread defaults to prevent stale fields from partial configs
  if (config.transcode) Object.assign(transcode, { ...DEFAULT_TRANSCODE, ...config.transcode })
  if (config.filters) Object.assign(filters, { ...DEFAULT_FILTER, ...config.filters })
  if (config.clip) {
    Object.assign(clip, { ...DEFAULT_CLIP, ...config.clip })
    activeMode.value = "clip"              // <-- may be overwritten below
  }
  if (config.merge) {
    Object.assign(merge, { ...DEFAULT_MERGE, ...config.merge })
    activeMode.value = "merge"             // <-- may be overwritten below
  }
  if (config.avsmix) {
    Object.assign(avsmix, { ...DEFAULT_AVSMIX, ...config.avsmix })
    activeMode.value = "avsmix"            // <-- may be overwritten below
  }
  if (config.custom_command) {
    Object.assign(custom_command, { ...DEFAULT_CUSTOM, ...config.custom_command })
    activeMode.value = "custom"            // <-- final winner if all 4 are present
  }
}
```

---

## Appendix C: MergePage.vue - local config bypass

Source: `frontend/src/pages/MergePage.vue` lines 94-101

```typescript
async function handleAddToQueue(): Promise<void> {
  if (!canAddToQueue.value) return
  // Build CLEAN merge-only config: inherits transcode/filters but NOT global merge (intro/outro)
  // MergePage uses its OWN merge config completely independently
  const taskCfg: TaskConfigDTO = {
    transcode: { ...transcode },
    filters: { ...filters },
    merge: { ...mergeConfig },
    output_dir: "",
  }
  const added = await queue.addTasks([mergeConfig.file_list[0]], taskCfg)
  if (added.length > 0) {
    router.push("/task-queue")
  }
}
```

---

## Appendix D: AudioSubtitlePage.vue - direct shared state mutation

Source: `frontend/src/pages/AudioSubtitlePage.vue` lines 24-52

```typescript
const { avsmix, activeMode, toTaskConfig } = useGlobalConfig()

const configRef = computed(() => toTaskConfig())
const { commandText, errors, warnings, validating } = useCommandPreview(configRef)

function handleDropAudio(path: string) {
  avsmix.external_audio_path = path
}

function handleDropSubtitle(path: string) {
  avsmix.subtitle_path = path
}

// ...

onMounted(() => {
  activeMode.value = "avsmix"
})
```

---

## Appendix E: task_runner.py - config merge with task-local priority

Source: `core/task_runner.py` lines 111-122

```python
if config is not None:
    incoming = TaskConfig.from_dict(config)
    current = task.config
    # Preserve the task's sub-configs (merge, avsmix, clip, custom_command)
    # so that a merge task added from MergePage keeps its own merge config
    # rather than being overwritten by the global config (which may only
    # have intro/outro from the Config page).
    task.config = TaskConfig(
        transcode=incoming.transcode,
        filters=incoming.filters,
        clip=incoming.clip or current.clip,
        merge=current.merge or incoming.merge,         # task-local wins
        avsmix=current.avsmix or incoming.avsmix,       # task-local wins
        custom_command=current.custom_command or incoming.custom_command,  # task-local wins
        output_dir=incoming.output_dir or current.output_dir,
    )
```

---

## Appendix F: command_builder.py - priority dispatch (early return pattern)

Source: `core/command_builder.py` lines 1020-1031

```python
# Dispatch to mode-specific builders
# Phase 3.5: custom command checked first (user controls full command)
if config.custom_command:
    return build_custom_command(config, input_path, output_path)
# Phase 3.5.2: intro/outro takes a single content file and wraps it
if config.merge and (config.merge.intro_path or config.merge.outro_path):
    return build_merge_intro_outro_command(config, input_path, output_path)
if config.merge and len(config.merge.file_list) >= 2:
    return build_merge_command(config, output_path)
# Clip with copy codec: standalone path (no transcode/filters needed)
if config.clip and (config.clip.start_time or config.clip.end_time_or_duration) and config.clip.use_copy_codec:
    return build_clip_command(config, input_path, output_path, file_duration)

# ... standard path with avsmix at line 1090+ (only reached if no merge)
```

---

## Appendix G: command_builder.py - avsmix in standard path (dead code when merge active)

Source: `core/command_builder.py` lines 1090-1125

```python
# --- avsmix: inject extra inputs and map directives ---
if config.avsmix:
    avsmix = config.avsmix
    avsmix_inputs: list[str] = []
    map_directives: list[str] = []

    if avsmix.external_audio_path:
        avsmix_inputs.extend(["-i", _subprocess_quote(avsmix.external_audio_path)])
        if avsmix.replace_audio:
            map_directives.extend(["-map", "0:v", "-map", "1:a"])

    if avsmix.subtitle_path:
        avsmix_inputs.extend(["-i", _subprocess_quote(avsmix.subtitle_path)])
        map_directives.extend(["-map", "2:s", "-c:s", "mov_text"])
        if avsmix.subtitle_language:
            map_directives.extend(["-metadata:s:s:0", f"language={avsmix.subtitle_language}"])

    args = list(clip_time_args)
    args.extend(["-i", _subprocess_quote(input_path)])
    args.extend(extra_inputs)
    args.extend(avsmix_inputs)
    args.extend(transcode_args)
    args.extend(filter_args)
    args.extend(map_directives)
    args.extend(["-y", _subprocess_quote(output_path)])
    return args
```

This code is only reached in the "standard path" -- if `config.merge` has intro/outro or file_list, the function already returned via the early dispatch at lines 1023-1026.

---

## Appendix H: validate_config - existing checks (no merge+avsmix cross-check)

Source: `core/command_builder.py` lines 1165-1294

Existing validation rules:
- `audio_normalize` + `volume` -> warning
- `aspect_convert` + `crop/rotate/watermark` -> error (mutually exclusive)
- `video_codec=copy` + filters -> warning
- `audio_codec=copy` + `volume` -> warning
- `audio_codec=copy` + `audio_normalize` -> warning
- `merge` without 2+ files (and no intro/outro) -> error
- `filter_complex` without `target_resolution` -> warning
- `subtitle` without `subtitle_language` -> warning

No cross-check exists between `merge` and `avsmix`.
