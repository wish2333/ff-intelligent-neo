# Python 后端代码审计报告

**项目**: ff-intelligent-neo | **分支**: dev-2.2.1 | **范围**: 19 文件, ~7,000 行 Python
**审计日期**: 2026-04-28

---

## 一、CRITICAL (3)

| # | 类别 | 位置 | 问题 |
|---|------|------|------|
| C-1 | 线程安全 | `task_runner.py` + `models.py` | **Task 对象跨线程无锁直接修改** -- worker 线程更新 progress/log，主线程读取序列化，`ffmpeg_runner.py:139-141` 在 reader 线程中直接 append `task.log_lines`，无任何同步 |
| C-2 | 安全 | `auto_editor_api.py:296-320` | **下载 auto-editor 二进制无完整性校验** -- `urlretrieve` 下载 exe 后仅运行 `--version`，无 SHA-256 校验，可被中间人攻击替换 |
| C-3 | 错误处理 | `logging.py:30,50` | **日志初始化静默吞异常** -- 文件 sink 创建失败时 `except Exception: pass`，无任何提示 |

---

## 二、HIGH (15)

| # | 类别 | 位置 | 问题 |
|---|------|------|------|
| H-1 | 线程安全 | `task_runner.py:180-211,624-716` | stop_task 与 _run_task_inner 之间存在竞态，都尝试转换 task 状态并 pop proc |
| H-2 | 线程安全 | `ffmpeg_setup.py:25-26` | `_ffmpeg_override_path` 全局可变变量无锁保护，`switch_ffmpeg` 写 / `get_ffmpeg_path` 读可并发 |
| H-3 | 线程安全 | `main.py:48-64` | **懒初始化属性无线程安全** -- `_runner`、`_queue`、`_auto_editor`、`_preset_mgr` 使用 `hasattr` 双检锁但无 `threading.Lock`，可重复创建 |
| H-4 | 架构 | `main.py` | **FFmpegApi God Class (874行, 40+ expose 方法)** -- 违反单一职责，涵盖任务队列、文件对话框、设置、预设、FFmpeg、auto-editor |
| H-5 | 架构 | `command_builder.py` (1260行) | 最大文件，注册表 lambda 嵌套深，可读性差 |
| H-6 | 架构 | `auto_editor_api.py:503-511` | `_pending_auto_editor_tasks` 仅存内存，崩溃后丢失，导致任务无法重试 |
| H-7 | 安全 | `command_builder.py:1222-1260` | **build_output_path 无路径遍历检查** -- `../../etc/` 等 pattern 未拦截 |
| H-8 | 安全 | `main.py:474` | `os.startfile()` 传入用户路径，TOCTOU 竞争可执行恶意关联 |
| H-9 | 安全 | `main.py:133-271` | `add_tasks` 接受路径后无验证直接创建 Task，未检查文件是否存在 |
| H-10 | 安全 | `task_runner.py:158-170` | concat 合并模式中文件路径未转义单引号，可注入 FFmpeg 指令 |
| H-11 | 类型安全 | `batch_runner.py` (全文) | **引用不存在的 FileItem、PresetManager.resolve_command，TaskProgress 字段不匹配** -- 全文件为 1.x 遗留死代码 |
| H-12 | 资源管理 | `task_runner.py:158-176` | 临时文件创建与 executor.submit 之间异常时泄漏 |
| H-13 | 资源管理 | `ffmpeg_runner.py:113-212` | 进程 stderr/stdout 管道未显式关闭 |
| H-14 | 代码质量 | `main.py:554,578` | `creationflags=0x08000000` 魔数，应为 `subprocess.CREATE_NO_WINDOW` |
| H-15 | 代码质量 | `main.py:571` | ffprobe 路径通过 `replace("ffmpeg", "ffprobe")` 派生，已有 `get_ffprobe_path()` 可用 |

---

## 三、MEDIUM (18)

| # | 类别 | 问题摘要 |
|---|------|---------|
| M-1 | 安全 | `queue_state.json` 非原子写入（`path.write_text` vs config.py 的 temp+replace） |
| M-2 | 安全 | preset_id 未验证，`../../evil` 可写入任意路径 |
| M-3 | 安全 | 无 `--protocol_whitelist` 限制，FFmpeg 可发网络请求 |
| M-4 | 安全 | 下载 auto-editor URL 使用 branch tip 而非 commit hash 固定 |
| M-5 | 安全 | bridge `@expose` 装饰器将完整异常信息 `str(exc)` 返回前端 |
| M-6 | 线程安全 | `_pending_auto_editor_tasks` 无锁，`hasattr` + 赋值非原子 |
| M-7 | 线程安全 | `_ensure_loguru` 标志无锁保护 |
| M-8 | 架构 | 事件名为裸字符串，无中央常量注册 |
| M-9 | 架构 | 事件载荷结构未文档化，前后端隐式约定 |
| M-10 | 架构 | task_type 分散在 `start_task/stop_task/retry_task` 多处 `getattr` 判断 |
| M-11 | 架构 | `TaskRunner` 直接修改 Task 字段但未持有 queue lock |
| M-12 | 架构 | bridge `tick` 失败静默吞异常，事件队列可无限增长 |
| M-13 | 架构 | `load_settings` 每次调用都读磁盘无缓存 |
| M-14 | 架构 | 新增任务类型需改 6+ 文件，无抽象扩展点 |
| M-15 | 数据安全 | 终端状态转换（completed/failed）走 debounce 保存，崩溃可丢失 |
| M-16 | 代码质量 | 设置更新重复 7 字段样板代码，缺 `AppSettings.with_updates()` |
| M-17 | 代码质量 | `auto_editor_api.py` + `paths.py` 多处 `print()` 绕过日志系统 |
| M-18 | 代码质量 | `file_info.py` 使用 `__import__` 而非标准 import |

---

## 四、LOW (8)

| # | 问题摘要 |
|---|---------|
| L-1 | `batch_runner.py` 全文件死代码（与 H-11 重复标记） |
| L-2 | `_REGISTERED_FILTERS_*` 变量赋值后未使用 |
| L-3 | `batch_runner.py` PATH 环境变量日志泄露 |
| L-4 | `main.py` `fail_task` debug 方法暴露在生产中 |
| L-5 | `MergeConfig.file_list` 类型标注为裸 `tuple` |
| L-6 | `callable` 小写代替 `Callable`（不一致） |
| L-7 | `shlex` 导入为 `_shlex` 命名不规范 |
| L-8 | 预设文件加载无 schema 验证 |

---

## 五、正面发现

- 所有 `subprocess` 调用使用列表形式，**无 `shell=True`**
- 无 `eval()`/`exec()`/`pickle` 使用
- 无硬编码密钥/凭证
- `config.py` 使用 temp+atomic replace 原子写入
- 进程树终止正确使用 `taskkill /F /T`（Windows）和 `os.killpg`（Unix）
- auto-editor 输入验证较好（URL 拒绝、扩展名白名单、路径遍历检查）
- 编解码器使用白名单验证
- 任务状态机设计清晰正确

---

## 六、优先修复建议

### P0 -- 立即修复

1. **Task 对象线程安全** -- 添加 per-task Lock 或将所有 Task 变更收归 TaskQueue lock 下
2. **懒初始化线程安全** -- 添加 `threading.Lock` 双检锁
3. **删除 `batch_runner.py` 死代码**

### P1 -- 近期修复

4. **auto-editor 下载添加 SHA-256 校验**
5. **`build_output_path` 添加路径遍历防护**
6. **concat 列表文件转义单引号**
7. **`queue_state.json` 改为原子写入**
8. **终端状态转换立即保存（不走 debounce）**

### P2 -- 架构改进

9. **拆分 `FFmpegApi` God Class**
10. **auto-editor 参数存入 Task 实体（持久化）**
11. **引入任务类型分发器（策略模式）**
12. **事件名常量化 + 载荷类型定义**

---

## 七、统计

| 严重度 | 数量 |
|--------|------|
| CRITICAL | 3 |
| HIGH | 15 |
| MEDIUM | 18 |
| LOW | 8 |
| **合计** | **44** |

| 分类 | CRITICAL | HIGH | MEDIUM | LOW |
|------|----------|------|--------|-----|
| 线程安全 | 1 | 3 | 2 | 0 |
| 安全 | 1 | 4 | 5 | 0 |
| 架构 | 0 | 3 | 7 | 0 |
| 代码质量 | 0 | 2 | 2 | 3 |
| 资源管理 | 0 | 2 | 0 | 0 |
| 类型安全 | 0 | 1 | 0 | 1 |
| 错误处理 | 1 | 0 | 0 | 0 |
| 数据安全 | 0 | 0 | 1 | 0 |
| 死代码 | 0 | 1 | 0 | 3 |
