# Fix All Issues - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 12 reported issues across Queue, Config, Merge, A/V Mix, and Custom pages.

**Architecture:** Backend fixes in `main.py` (operator precedence), `command_builder.py` (filter_complex syntax, aspect_convert). Frontend fixes in `useGlobalConfig.ts` (cross-mode isolation), `FilterForm.vue` (context-aware fullscreen drop), `TranscodeForm.vue` (field ordering), `AudioSubtitlePage.vue` (click handlers), `MergeFileList.vue` (fullscreen drop).

**Tech Stack:** Python 3.10+, Vue 3 + TypeScript, pywebview, FFmpeg

---

## Task 1: Fix Queue Upload - Operator Precedence in main.py

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\main.py:169-204`

**Root Cause:** In `add_tasks()`, line 171 has:
```python
if clip_data and clip_data.get("start_time") or clip_data.get("end_time_or_duration"):
```
Python operator precedence evaluates this as `(clip_data and clip_data.get("start_time")) or clip_data.get("end_time_or_duration")`. When `clip_data` is `None`, first part is `None`, then `None or clip_data.get(...)` fails with `'NoneType' object has no attribute 'get'`.

The same issue exists for `avsmix_data` at line 189.

- [ ] **Fix operator precedence** - Add parentheses: `if clip_data and (clip_data.get("start_time") or clip_data.get("end_time_or_duration")):` and same for `avsmix_data`

## Task 2: Refactor useGlobalConfig.ts for Cross-Mode Isolation

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useGlobalConfig.ts`
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\MergePage.vue`

**Root Cause:** `configRef` includes `merge` when `merge.intro_path || merge.outro_path` is truthy even when current mode is NOT "merge". This causes Config/A/V Mix pages to inherit merge preview.

- [ ] **Change configRef to be strictly mode-based** - Only include merge when activeMode === "merge"
- [ ] **Update MergePage.vue** - Build its own config inheriting transcode + filters from shared state

## Task 3: Fix Config - Merge Intro/Outro Support Single File + Default FilterComplex

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\MergeSettingsForm.vue`
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\composables\useGlobalConfig.ts`

- [ ] **Auto-switch merge_mode to filter_complex** when intro_path or outro_path is set
- [ ] **Support independent intro/outro** - Already supported, verify no blocking

## Task 4: Fix Config - Transcode Field Ordering

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\TranscodeForm.vue`

**Current:** Column 1 has Video Codec, Resolution, Framerate, Quality, Quality Value. Column 2 has Bitrates, Preset, Pixel Format.

**Required:** Top section = Resolution, Framerate, Quality Mode, Quality Value. Bottom = Bitrates, Preset, Pixel Format.

- [ ] **Restructure columns** - Move Resolution/Framerate/QM/QV together, VB/MB/EP/PF together

## Task 5: Fix Config - Aspect Ratio Convert Preview

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\core\command_builder.py`
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\FilterForm.vue`

**Root Cause:** When `aspect_convert` is set but `target_resolution` is empty, `_build_aspect_convert_filter` returns `[], []`, showing no preview.

- [ ] **Auto-fill default target_resolution** when aspect_convert is selected and resolution is empty
- [ ] **Ensure aspect_convert filter triggers preview update** through the reactive chain

## Task 6: Fix Config - Filters Fullscreen Drag Context-Dependent

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\FilterForm.vue`

**Root Cause:** Watermark FileDropInput has `fullscreen-drop` and is `v-show`/class-disabled instead of `v-if` when aspect_convert is active. Two FileDropInput instances with fullscreen-drop can conflict.

**Required:**
- No aspect convert → fullscreen drop → Watermark Image
- Aspect convert (H2V-I/V2H-I) → fullscreen drop → Background Image
- Aspect convert (H2V-B/V2H-B/H2V-T/V2H-T) → no fullscreen drop, hide bg area

- [ ] **Use `v-if` instead of class/opacity for watermark section** when aspect_convert is active
- [ ] **Conditionally set fullscreen-drop prop** on correct FileDropInput

## Task 7: Fix Merge Page - Fullscreen Drag-Drop

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\MergePanel.vue`
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\MergeFileList.vue`

- [ ] **Add fullscreen drag-drop support** to MergeFileList for adding video files
- [ ] **Support add/clear** via fullscreen drop

## Task 8: Fix Merge Page - File Identification (Duplicate/Order)

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\components\config\MergeFileList.vue`

**Root Cause:** The "same file twice" issue occurs when `MergeFileList.vue`'s `addFiles` function is called multiple times or already-selected files are re-selected. The order issue happens when files are reordered but the update doesn't propagate to the preview.

- [ ] **Add deduplication** - Don't add files already in the list
- [ ] **Ensure order is preserved** through the reactivity chain

## Task 9: Fix Merge Page - 3+ Files Preview (Filter Complex Syntax)

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\core\command_builder.py:725-726`

**Root Cause:** `build_merge_command` uses commas between concat input labels:
```python
f"{''.join(f'[v{i}],' for i in range(n))}concat=..."
```

This produces `[v0],[v1],[v2],concat=n=3:...` which is incorrect FFmpeg filter syntax. The correct syntax is `[v0][v1][v2]concat=n=3:v=1:a=1` (no commas).

Fix: Remove trailing commas in `join`:
```python
f"{''.join(f'[v{i}]' for i in range(n))}concat=n={n}:v=1:a=1[vout]"
```

- [ ] **Fix concat filter syntax** - Remove commas between input labels
- [ ] **Verify for N=2,3,4 cases**

## Task 10: Fix Merge Page - Delete File Preview Update

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\MergePage.vue`

**Root Cause:** `MergePage.vue` uses `configRef = computed(() => toTaskConfig())` which uses the global `configRef`. After the cross-mode refactor, merge config is only included when mode === "merge". May need additional reactivity triggers.

- [ ] **Verify reactivity** - Ensure file_list changes trigger command preview update

## Task 11: Fix A/V Mix Page - Click to Open File Selector

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\frontend\src\pages\AudioSubtitlePage.vue`

**Root Cause:** The audio and subtitle card divs have `class="cursor-pointer"` but no `@click` handler to open file dialog.

- [ ] **Add click handlers** - `handleClickAudio()` and `handleClickSubtitle()` calling `select_files`
- [ ] **Add @click to both card divs**

## Task 12: Fix Custom Page - Parameter Override

**Files:**
- Modify: `Q:\Git\GithubManager\ff-intelligent-neo\core\command_builder.py:918-919`

**Root Cause:** Already checked first in `build_command()`:
```python
if config.custom_command:
    return build_custom_command(config, input_path, output_path)
```
This should correctly prioritize custom_command. But `build_command_preview` needs to verify custom command is shown correctly.

- [ ] **Add backend-side build_custom_command_preview** for consistency
- [ ] **Fix local preview in CustomCommandPage.vue**

---

## Manual Test Plan

```
## Queue Page
- [ ] Upload single file - no error
- [ ] Upload multiple files - all added correctly
- [ ] Upload file with special characters - handles correctly

## Config Page
- [ ] Transcode: Resolution, Framerate, QM, QV at top
- [ ] Transcode: VB, MB, EP, PF at bottom
- [ ] Filters: Aspect Ratio Convert shows preview when selected
- [ ] Filters: No aspect convert → fullscreen drag → watermark
- [ ] Filters: Aspect convert (H2V-I/V2H-I) → fullscreen drag → bg image
- [ ] Filters: Aspect convert (H2V-B/H2V-T) → no fullscreen drag, no bg image
- [ ] Merge tab: Can add only intro (no outro)
- [ ] Merge tab: Default mode auto-switches to filter_complex

## Merge Page
- [ ] Fullscreen drag-drop adds files to list
- [ ] File list order preserved in command preview
- [ ] Add 3+ files - all appear in command preview
- [ ] Delete file - command preview updates
- [ ] Command preview independent from Config page
- [ ] Command preview inherits transcode settings from Config

## A/V Mix Page
- [ ] Click audio region - opens file selector
- [ ] Click subtitle region - opens file selector
- [ ] Split-screen drag-drop works

## Custom Page
- [ ] Enter raw args - overrides other params
- [ ] Preview shows custom command only

## Cross-Mode
- [ ] Config page changes don't affect Merge page preview
- [ ] Merge page changes don't affect Config page preview
- [ ] A/V Mix and Custom share config with Config
```
