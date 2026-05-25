# Audit Fix Plan v2.2.4 - Minimal Implementation Path

- Date: 2026-05-25
- Based on: `docs/audit-report-2.2.4.md` + architect feedback
- Principle: minimal diff, no architecture overhaul, fix what's broken

---

## Architect Feedback Evaluation

The architect proposed a multi-step temp file approach for intro/outro + avsmix coexistence. After code review, this approach is **rejected** for the following reasons:

1. `build_merge_intro_outro_command` (line 852) uses FFmpeg `filter_complex` to concat intro + content + outro in a **single pass**. It already handles audio normalization via `aformat=sample_rates=44100:channel_layouts=stereo`. Injecting avsmix (external audio/subtitle) into this pipeline is technically feasible but would require rewriting the filter_complex builder -- high risk, low reward.
2. The current single-command-per-task architecture means `build_command_preview` must match `build_command` exactly. Multi-step execution would break this guarantee.
3. The real-world use case (add intro/outro AND replace audio simultaneously) is rare. A clear validation warning is the correct minimal fix.

**Adopted from architect**: validate_config cross-check, task_runner priority fix, loadFromTaskConfig reset, UI rename.

---

## Phase 1: Frontend - useGlobalConfig.ts (Issues #2, #4)

> **Variable naming confirmed**: The reactive variable is `customCommand` (camelCase, line 88),
> the DTO field is `custom_command` (snake_case, line 162). `Object.assign(customCommand, ...)`
> targets the reactive variable correctly. No naming bug exists.

### 1a. Fix loadFromTaskConfig: add reset + priority-based activeMode

**File**: `frontend/src/composables/useGlobalConfig.ts` lines 149-169

**Change**: Reset all sub-configs and activeMode at the top, then use if/else-if chain with priority: custom > merge(concat) > avsmix > clip > merge(intro/outro only) > transcode.

```typescript
function loadFromTaskConfig(config: TaskConfigDTO) {
  // Reset sub-configs to prevent stale fields (Issue #4)
  Object.assign(clip, DEFAULT_CLIP)
  Object.assign(merge, DEFAULT_MERGE)
  Object.assign(avsmix, DEFAULT_AVSMIX)
  Object.assign(customCommand, DEFAULT_CUSTOM)
  activeMode.value = "transcode"

  if (config.transcode) Object.assign(transcode, { ...DEFAULT_TRANSCODE, ...config.transcode })
  if (config.filters) Object.assign(filters, { ...DEFAULT_FILTER, ...config.filters })

  // Priority-based activeMode selection (Issue #2)
  if (config.custom_command) {
    Object.assign(customCommand, { ...DEFAULT_CUSTOM, ...config.custom_command })
    activeMode.value = "custom"
  } else if (config.merge && config.merge.file_list?.length >= 2) {
    Object.assign(merge, { ...DEFAULT_MERGE, ...config.merge })
    activeMode.value = "merge"
  } else if (config.avsmix) {
    Object.assign(avsmix, { ...DEFAULT_AVSMIX, ...config.avsmix })
    activeMode.value = "avsmix"
  } else if (config.clip) {
    Object.assign(clip, { ...DEFAULT_CLIP, ...config.clip })
    activeMode.value = "clip"
  } else if (config.merge) {
    // Intro/outro only -- stays on transcode page, merge config loaded as global setting
    Object.assign(merge, { ...DEFAULT_MERGE, ...config.merge })
  }
}
```

**Risk**: LOW. Existing callers (preset load, task edit) all pass complete configs. The reset-then-assign pattern matches what `resetAll()` already does.

### 1b. Extract createBaseTaskConfig helper

**File**: `frontend/src/composables/useGlobalConfig.ts`

**Change**: Add and export a `createBaseTaskConfig` function. MergePage will use this instead of hand-writing the base.

```typescript
function createBaseTaskConfig(): TaskConfigDTO {
  return {
    transcode: { ...transcode },
    filters: { ...filters },
    output_dir: "",
  }
}
```

Add to the return object alongside existing exports.

**Risk**: NONE. Purely additive, no existing code changes.

---

## Phase 2: Frontend - MergePage.vue (Issue #5)

**File**: `frontend/src/pages/MergePage.vue` lines 94-101

**Change**: Replace hand-written base config with `createBaseTaskConfig()`.

```typescript
const { transcode, filters, activeMode, createBaseTaskConfig } = useGlobalConfig()

// ...

async function handleAddToQueue(): Promise<void> {
  if (!canAddToQueue.value) return
  const taskCfg: TaskConfigDTO = {
    ...createBaseTaskConfig(),
    merge: { ...mergeConfig },
  }
  const added = await queue.addTasks([mergeConfig.file_list[0]], taskCfg)
  if (added.length > 0) {
    router.push("/task-queue")
  }
}
```

**Risk**: LOW. Functionally identical to current code, just uses shared helper.

---

## Phase 3: Backend - validate_config cross-check (Issue #6)

**File**: `core/command_builder.py` lines 1260-1280 (inside `validate_config`, after existing avsmix check)

**Change**: Add merge+avsmix coexistence warning.

```python
# After existing avsmix validation block:
if config.avsmix and config.merge:
    has_intro_outro = config.merge.intro_path or config.merge.outro_path
    has_concat = len(config.merge.file_list) >= 2
    if has_concat:
        issues.append({
            "level": "error",
            "param": "merge",
            "message": "Multi-file concat and audio/subtitle mixing cannot coexist. "
                       "Process merge first, then apply audio/subtitle to the result.",
        })
    elif has_intro_outro:
        issues.append({
            "level": "warning",
            "param": "avsmix",
            "message": "Intro/outro wrapping will ignore audio/subtitle settings. "
                       "The intro/outro pipeline uses its own audio normalization.",
        })
```

**Risk**: LOW. Validation-only, no execution path changes.

---

## Phase 4: Backend - task_runner merge priority (Issue #3)

**File**: `core/task_runner.py` lines 111-122

**Change**: Allow global intro/outro to apply to non-concat tasks, but preserve task-local intro/outro when present.

The architect identified a short-circuit hazard in the original plan: `incoming.merge or current.merge` would overwrite a task's own intro/outro with the global one. The correct logic is:
- Concat tasks (file_list >= 2): always keep local merge config
- Tasks with local intro/outro: keep local (task-specific takes priority)
- Tasks with no local merge: inherit global intro/outro

```python
if config is not None:
    incoming = TaskConfig.from_dict(config)
    current = task.config

    # Merge resolution strategy:
    # 1. Multi-file concat tasks always keep their own merge config
    # 2. Tasks with their own intro/outro keep theirs (local wins)
    # 3. Tasks with no merge config inherit global intro/outro
    has_local_concat = current.merge and len(current.merge.file_list) >= 2
    if has_local_concat:
        resolved_merge = current.merge
    else:
        has_local_intro_outro = current.merge and (current.merge.intro_path or current.merge.outro_path)
        resolved_merge = current.merge if has_local_intro_outro else incoming.merge

    task.config = TaskConfig(
        transcode=incoming.transcode,
        filters=incoming.filters,
        clip=incoming.clip or current.clip,
        merge=resolved_merge,
        avsmix=current.avsmix or incoming.avsmix,
        custom_command=current.custom_command or incoming.custom_command,
        output_dir=incoming.output_dir or current.output_dir,
    )
```

**Risk**: MEDIUM. Changes runtime behavior for existing tasks. MergePage tasks always have `file_list >= 2` (enforced by `canAddToQueue` at line 47), so they hit the `has_local_concat` branch. AudioSubtitlePage and CommandConfigPage tasks have empty `file_list`, so they correctly fall through to the intro/outro inheritance path.

---

## Phase 5: Frontend - UI rename + tips (Issue #7)

**File**: `frontend/src/components/config/MergeSettingsForm.vue`, `frontend/src/pages/CommandConfigPage.vue`, i18n files

**Changes**:
1. Rename the Config page tab from "Merge" / "视频合并" to "Intro/Outro" / "片头片尾" (i18n key change)
2. Add a tips banner at the top of MergeSettingsForm:

```
Tip: Intro/outro configured here is a global batch template, automatically applied to
normal transcode and filter tasks in the queue.
- Note: If a task also has Audio/Subtitle Mixing (AVSMix) enabled, the global intro/outro
  will be ignored due to FFmpeg pipeline limitations.
- Multi-video merge: Use the dedicated "Video Merge" page in the left navigation.
```

This aligns with the Phase 3 backend validation warnings and proactively sets user expectations.

**Risk**: NONE. Text-only changes.

---

## Files Modified (Summary)

| File | Phase | Changes |
|------|-------|---------|
| `frontend/src/composables/useGlobalConfig.ts` | 1a, 1b | Fix loadFromTaskConfig, add createBaseTaskConfig |
| `frontend/src/pages/MergePage.vue` | 2 | Use createBaseTaskConfig |
| `core/command_builder.py` | 3 | Add merge+avsmix validation |
| `core/task_runner.py` | 4 | Fix merge priority for intro/outro |
| `frontend/src/components/config/MergeSettingsForm.vue` | 5 | UI text update |
| `frontend/src/pages/CommandConfigPage.vue` | 5 | Tab label update |

## Architect Feedback Incorporated

| Feedback | Status |
|----------|--------|
| Variable name `customCommand` vs `custom_command` | Verified correct -- reactive var is camelCase, DTO field is snake_case |
| `createBaseTaskConfig` must be in return object | Noted -- will add to return block |
| task_runner short-circuit overwrite hazard | Fixed -- 3-tier resolution: concat > local intro/outro > global |
| UI tips for MergeSettingsForm | Added to Phase 5 |
| Error vs warning blocking behavior | Verified -- `CommandPreview` is display-only, neither errors nor warnings block `addTasks`. Acceptable for minimal fix. |

## Blocking Behavior Note

Current frontend architecture: `validate_config` errors/warnings are rendered by `CommandPreview` as visual indicators only. Neither level blocks task submission (`addTasks`). This means:

- `warning` (intro/outro + avsmix): shows yellow indicator, user can still submit. avsmix will be silently ignored by backend. **Acceptable** -- the warning sets expectation.
- `error` (concat + avsmix): shows red indicator, user can still submit. avsmix will be silently ignored by backend. **Acceptable for now** -- strong visual signal. Frontend blocking can be added as follow-up if needed.

## Verification Matrix

| Test Case | Expected Behavior | Validates |
|-----------|-------------------|-----------|
| A: Add 2 concat tasks from MergePage, then modify global intro/outro | Concat tasks keep their `file_list`, no intro/outro applied | `has_local_concat` isolation |
| B: Add normal task, set global intro/outro on Config page | Command preview shows `-filter_complex` concat params | Global intro/outro inheritance |
| C: Load preset with both `clip` and `avsmix` data | Page highlights AudioSubtitlePage (avsmix priority), clip data still loaded | Priority-based `activeMode` |
| D: On AudioSubtitlePage with avsmix set, also set global intro/outro | Warning appears in command preview | Phase 3 validation cross-check |
| E: `cd frontend && bun run build` | Type check passes | No regressions |
| F: `uv run pytest test/` | All tests pass | Backend changes safe |

## What We Explicitly Do NOT Do

1. **Multi-step temp file execution** -- architect's proposal rejected. Too complex for the marginal benefit. The validation warning (Phase 3) is the correct minimal fix.
2. **Rewrite build_command dispatch** -- the early-return pattern is correct for the current feature set. Adding avsmix support inside `build_merge_intro_outro_command` would require rewriting the filter_complex builder and breaking the single-command guarantee.
3. **Pinia migration** -- the module-level reactive singleton pattern works correctly for this app's scale. The issues are logic bugs, not architecture problems.

## Verification

After all phases:
- `cd frontend && bun run build` -- type check passes
- `uv run pytest test/` -- backend tests pass
- Manual test: set global intro/outro on Config page, then go to AudioSubtitlePage and set external audio. Verify the validation warning appears in the command preview.
- Manual test: load a preset with both clip and avsmix. Verify activeMode resolves to "avsmix" (not "clip").
