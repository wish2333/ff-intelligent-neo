# Implementation Plan v2.2.6 - Task Queue Page Fixes

**Date**: 2026-06-10
**Based on**: `docs/audit-report-2.2.6.md` (Architect-approved)
**Status**: Ready for Development
**Branch**: `dev-2.2.5` -> `fix/2.2.6-queue-ux`

---

## Product Decision (Confirmed)

| Dimension | Decision | Rationale |
|-----------|----------|-----------|
| Storage order | FIFO unchanged (oldest at index 0, newest at end) | Backend stays as-is |
| Display order | Oldest-top, newest-bottom (same as current) | No reorder needed |
| Execution order | FIFO -- oldest tasks execute first | Natural queue semantics |
| Scroll position | **Auto-scroll to bottom** on load and after adding tasks | User sees newest tasks first |
| Scrollbar fix | Enable overflow-y-auto + sticky header (Issue 2) | Independent of ordering |

**Net effect**: User opens the page -> scrolled to bottom -> sees newest tasks. Scrolls up to see older tasks. No backend changes needed.

---

## Implementation Tasks

### Task 1: Frontend -- Auto-scroll to bottom (Issue 1 replacement)

**Files**: `frontend/src/components/task-queue/TaskList.vue`, `frontend/src/pages/TaskQueuePage.vue`
**Risk**: Low (view-only behavior, no data changes)
**Tests**: Manual verification

#### Change 1a: `TaskList.vue` -- Add scroll container ref + expose scrollToBottom

```html
<!-- BEFORE -->
<div class="flex-1 overflow-hidden rounded-lg border border-base-300">

<!-- AFTER: add ref, change to overflow-y-auto (also needed for Issue 2) -->
<div ref="scrollContainer" class="flex-1 overflow-y-auto rounded-lg border border-base-300">
```

```ts
// Add to <script setup>
import { ref } from "vue"
import { nextTick } from "vue"

const scrollContainer = ref<HTMLElement | null>(null)

/** Scroll the task list to the bottom (newest tasks). */
async function scrollToBottom(): Promise<void> {
  await nextTick()
  const el = scrollContainer.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

// Expose to parent
defineExpose({ scrollToBottom })
```

#### Change 1b: `TaskQueuePage.vue` -- Call scrollToBottom after add and on mount

```ts
// Add template ref for TaskList
const taskListRef = ref<InstanceType<typeof TaskList> | null>(null)

// In handleAddFiles -- scroll after adding
async function handleAddFiles(): Promise<void> {
  // ... existing file selection logic ...
  await queue.addTasks(res.data, globalConfig.toTaskConfig())
  taskListRef.value?.scrollToBottom()  // <-- NEW: scroll to see newest
}

// In handleDrop -- scroll after adding
async function handleDrop(): Promise<void> {
  // ... existing drop logic ...
  await queue.addTasks(paths, globalConfig.toTaskConfig())
  taskListRef.value?.scrollToBottom()  // <-- NEW: scroll to see newest
}

// In onMounted -- scroll after initial load
onMounted(async () => {
  try {
    await waitForPyWebView()
    await Promise.all([queue.fetchTasks(), queue.fetchSummary()])
  } catch (err) {
    logError("TaskQueuePage", "mount failed", err)
  } finally {
    isReady.value = true
    // Scroll to bottom after initial render so user sees newest tasks
    await nextTick()
    taskListRef.value?.scrollToBottom()
  }
})
```

```html
<!-- Template: add ref to TaskList -->
<TaskList
  ref="taskListRef"
  :tasks="queue.tasks.value"
  ...
/>
```

#### Verification Checklist

- [ ] Open app with existing tasks -> auto-scrolled to bottom (newest visible)
- [ ] Add files via button -> list scrolls to bottom to show newly added tasks
- [ ] Drop files -> list scrolls to bottom
- [ ] User manually scrolls up -> stays at that position (no forced scroll)
- [ ] Empty queue -> no error, no scroll attempt

---

### Task 2: Frontend -- Enable vertical scrolling with sticky header (Issue 2)

**Files**: `frontend/src/components/task-queue/TaskList.vue`, `frontend/src/pages/TaskQueuePage.vue`
**Risk**: Low (CSS-only changes)
**Tests**: Manual visual verification

> Note: `overflow-y-auto` change on TaskList is already included in Task 1a.
> This task covers the remaining CSS changes.

#### Change 2a: `TaskList.vue` -- Pin table header during scroll

```html
<!-- BEFORE -->
<thead>
  <tr>...</tr>
</thead>

<!-- AFTER -->
<thead class="sticky top-0 z-10 bg-base-200 shadow-sm">
  <tr>...</tr>
</thead>
```

**CSS class rationale:**
| Class | Purpose |
|-------|---------|
| `sticky top-0` | Pins header at top of scroll container |
| `z-10` | Ensures header renders above scrolled `<tbody>` rows |
| `bg-base-200` | Opaque background covers rows underneath |
| `shadow-sm` | Subtle depth to visually separate header from scrolled content |

#### Change 2b: `TaskQueuePage.vue` -- Remove outer scroll to prevent double scrollbar

```html
<!-- BEFORE -->
<div class="page-scroll flex min-h-0 flex-1 flex-col gap-3 p-4 overflow-y-auto">

<!-- AFTER -->
<div class="page-scroll flex min-h-0 flex-1 flex-col gap-3 p-4">
```

Remove `overflow-y-auto` from the page container. The TaskList becomes the sole scroll context. Toolbar and summary are always visible.

#### Verification Checklist

- [ ] Few tasks (no overflow) -> no scrollbar, looks identical to before
- [ ] Many tasks (20+) -> vertical scrollbar appears in task list area
- [ ] Scroll down -> table header stays pinned, column labels visible
- [ ] Scroll up -> header still pinned at top, content scrolls beneath it
- [ ] Resize window very small -> only task list scrolls, toolbar/summary stay fixed
- [ ] No double scrollbar appears at any viewport size
- [ ] Open log panel -> log content doesn't conflict with task list scroll
- [ ] Empty state (0 tasks) -> empty state message centered correctly

---

## Execution Order

```
Task 1 (auto-scroll) + Task 2 (sticky header) -- can be done together
        |
        v
  Both modify the same 2 files (TaskList.vue + TaskQueuePage.vue)
```

Since both tasks modify `TaskList.vue` and `TaskQueuePage.vue`, implement them together in a single pass to avoid merge conflicts.

---

## Files Modified Summary

| File | Task | Change | Lines |
|------|------|--------|-------|
| `frontend/src/components/task-queue/TaskList.vue` | 1+2 | Add `ref`, expose `scrollToBottom`, `overflow-y-auto`, sticky `<thead>` | ~12 lines |
| `frontend/src/pages/TaskQueuePage.vue` | 1+2 | Add `taskListRef`, call `scrollToBottom` in 3 places, remove `overflow-y-auto` | ~6 lines |

**Total**: 2 files, ~18 lines. Zero backend changes.

---

## Regression Risk Matrix

| Scenario | Task 1 (auto-scroll) | Task 2 (CSS) |
|----------|---------------------|--------------|
| Add single task | Auto-scrolls to bottom | None |
| Add batch tasks | Auto-scrolls to bottom | None |
| Initial page load | Auto-scrolls to bottom | None |
| User manual scroll | No forced re-scroll | None |
| Start / Stop / Pause | No scroll interference | None |
| Move up / Move down | No scroll interference | None |
| Queue persistence | None (view-only) | None |
| App restart | Scroll to bottom on reload | None |
| Many tasks overflow | Scrollbar now visible | New scrollbar behavior |
| Resize window small | None | Flex layout may shift |
| Log panel open | None | z-index interaction possible |
| Empty queue | No scroll attempt | None |

---

## Post-Implementation Verification

```bash
# 1. Run existing backend tests (no backend changes, but sanity check)
uv run pytest test/ -v

# 2. Build frontend type check
cd frontend && bun run build

# 3. Start the app
uv run dev.py

# 4. Manual test scenarios:
#    a. Open app with existing tasks -> verify scrolled to bottom
#    b. Add 5+ files -> verify list scrolls to show newest
#    c. Add another batch -> verify scrolls again
#    d. Manually scroll up -> verify position holds
#    e. Scroll through 20+ tasks -> verify sticky header
#    f. Resize window small -> verify no double scrollbar
#    g. Move tasks up/down -> verify reorder works + no forced scroll
#    h. Start All Pending -> verify execution from oldest (top)
```
