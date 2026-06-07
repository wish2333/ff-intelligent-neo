# 更新记录 v2.2.4

- 日期: 2026-05-25
- 分支: dev-2.2.4
- 类型: 修复 (fix) + 重构 (refactor)

---

## 变更概述

修复音视频混流页（AudioSubtitlePage）与配置页（CommandConfigPage）之间的组合冲突逻辑，消除 7 个审计发现的架构缺陷。

## 变更详情

### 1. 修复 loadFromTaskConfig 状态残留与模式覆盖 (HIGH)

**文件**: `frontend/src/composables/useGlobalConfig.ts`

- 加载预设或编辑任务时，先重置 clip/merge/avsmix/customCommand 到默认值，再按优先级决定 activeMode
- 优先级: custom > merge(多文件拼接) > avsmix > clip > merge(仅片头片尾) > transcode
- 修复了加载同时包含 clip 和 avsmix 的预设时，activeMode 被最后一个匹配项覆盖的问题

### 2. 新增 createBaseTaskConfig 公共基础配置函数 (LOW)

**文件**: `frontend/src/composables/useGlobalConfig.ts`

- 导出 `createBaseTaskConfig()` 函数，返回包含 transcode + filters + output_dir 的基础 TaskConfigDTO
- MergePage 使用此函数替代手写基础配置，确保所有页面的公共参数源自同一血统

### 3. MergePage 使用公共基础配置 (LOW)

**文件**: `frontend/src/pages/MergePage.vue`

- `handleAddToQueue` 中使用 `createBaseTaskConfig()` 替代手动展开 transcode/filters

### 4. 新增 merge + avsmix 共存校验 (HIGH)

**文件**: `core/command_builder.py`

- `validate_config` 新增跨配置校验:
  - 多文件拼接 (file_list >= 2) + avsmix 共存 → error（阻断级）
  - 片头片尾 (intro/outro) + avsmix 共存 → warning（提示级）
- 修复了 merge 和 avsmix 同时存在时 avsmix 被静默忽略、用户无任何提示的问题

### 5. 修复 task_runner 合并优先级策略 (MEDIUM)

**文件**: `core/task_runner.py`

- 原逻辑 `current.merge or incoming.merge` 会导致全局片头片尾覆盖任务本地配置
- 新逻辑采用三层判定:
  1. 多文件拼接任务 (file_list >= 2) → 保留任务本地配置
  2. 任务自带片头片尾 → 保留任务本地配置（本地优先）
  3. 无本地 merge 配置 → 继承全局片头片尾

### 6. 配置页标签重命名 + 使用提示 (LOW)

**文件**: `frontend/src/components/config/MergeSettingsForm.vue`, `frontend/src/i18n/locales/en.ts`, `frontend/src/i18n/locales/zh-CN.ts`

- 配置页标签从 "Merge"/"合并" 更名为 "Intro / Outro"/"片头片尾"
- MergeSettingsForm 顶部新增信息提示横幅:
  - 说明全局片头片尾的作用范围
  - 提示 avsmix 与片头片尾的管线冲突
  - 引导用户前往专用的视频合并页面

---

## 变更文件清单

| 文件 | 变更类型 |
|------|----------|
| `frontend/src/composables/useGlobalConfig.ts` | 修复 + 新增 |
| `frontend/src/pages/MergePage.vue` | 重构 |
| `core/command_builder.py` | 新增校验 |
| `core/task_runner.py` | 修复 |
| `frontend/src/components/config/MergeSettingsForm.vue` | UI 更新 |
| `frontend/src/i18n/locales/en.ts` | 文案更新 |
| `frontend/src/i18n/locales/zh-CN.ts` | 文案更新 |

---

## Commit Message

```
fix: 修复音视频混流与配置页组合冲突逻辑

- 修复 loadFromTaskConfig 状态残留，采用 reset + 优先级链决定 activeMode
- 新增 merge+avsmix 共存校验（concat 为 error，intro/outro 为 warning）
- 修复 task_runner 合并优先级，三层判定防止全局配置覆盖任务本地配置
- 配置页 Merge 标签重命名为 Intro/Outro，新增使用引导提示
- 导出 createBaseTaskConfig 公共函数统一基础配置来源
```

---

## Release Notes

### 修复

- **配置加载状态残留**: 加载预设或编辑任务时，残留的旧模式状态不再干扰当前页面高亮
- **混流静默丢失**: 同时设置片头片尾和音频/字幕混流时，命令预览现在会显示明确的警告提示，而非静默忽略混流设置
- **全局配置覆盖任务配置**: 全局片头片尾不再覆盖队列中已有独立片头片尾的任务配置

### 改进

- **配置页标签**: "合并" 标签更名为 "片头片尾"，更准确反映其功能定位
- **使用引导**: 片头片尾设置区域新增信息提示，说明与音频/字幕混流的冲突关系及多视频合并的正确入口

---

## 验证结果

- 前端 `bun run build` 类型检查 + 生产构建: 通过
- 后端 87 项测试: 86 通过，1 项预存失败（AS-01 auto-editor Windows 兼容性问题，与本次变更无关）
