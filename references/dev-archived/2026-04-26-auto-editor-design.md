# Auto-Editor Integration Design

**Date:** 2026-04-26  
**Status:** Revised (2026-04-26, Audit Round 5 - P0/P1 issues fixed)
**Branch:** dev-2.2.0

---

## Revision History

| Date | Revision | Description |
|------|----------|-------------|
| 2026-04-26 | v1.0 | Initial approved design |
| 2026-04-26 | v1.1 | Round 1 audit fixes: API decoupling, security (shell=False, injection prevention), ffmpeg dependency, test strategy |
| 2026-04-26 | v1.2 | Round 2 audit fixes: params consistency (input_file), event mechanism, parse_output details, settings persistence, test CI segregation, downloader security |
| 2026-04-26 | v1.3 | Round 3 P0 fixes: remove --ffmpeg-location, fix subtitle pattern, fix progress machine mode with \r parsing, fix output path, unify API return types, fix CommandPreview format, remove "Run Now" button |
| 2026-04-26 | v1.4 | Round 4 P0 fixes: fix encoder cmd (-encoders not --encoders, requires format param), fix parse_output (\r handling, float progress, eta_seconds), fix task_runner chunk-based reading, add URL rejection, fix multi-range flags, fix output extension, fix display format |
| 2026-04-26 | v1.5 | Round 5 P0/P1 fixes: encoder API structured output + format validation, command build ownership clarified (API validate/enqueue only), task_runner stream parser per task type, when-normal supports cut, version compatibility check, NO_COLOR env, cancel task contract, single file limit, audio-only motion check, output atomic path, --open queue warning |

---

目前版本基于https://github.com/WyattBlue/auto-editor/releases/tag/30.1.4此版本的auto-editor进行

## 1. Architecture Overview

The design follows the exact same architecture as the existing FFmpeg integration, with **independent API class**:

```
Frontend (Vue 3)                    Backend (Python)                    Task Queue
─────────                            ────────────                      ───────────
AutoCutPage.vue                       AutoEditorApi (main.py)
  ├─ BasicTab.vue                    ├─ @expose run_auto_editor()
  ├─ AdvancedTab.vue                 ├─ @expose get_auto_editor_version()
  ├─ useAutoEditor.ts               ├─ @expose set_auto_editor_path()
  └─ useCommandPreview (shared)      └─ @expose preview_auto_editor_command()
                                              │
                                              ▼
                                      auto_editor_runner.py
                                       ├─ build_command(params, ffmpeg_path)
                                       ├─ run_auto_editor(path, params)
                                       └─ parse_output(line) → dict
                                              │
                                              ▼
                                      task_runner.py (shared)
                                       └─ reads proc.stdout/stderr
                                          └─ queue.emit('task_progress')
                                             └─ queue.emit('task_complete')
                                                    │
                                                    ▼
                                            Frontend task-queue components
                                            (shared progress/log display)
```

**Key decisions:**
- New page `AutoCutPage.vue` with `BasicTab.vue` + `AdvancedTab.vue`
- New composable `useAutoEditor.ts` for state management
- New backend module `auto_editor_runner.py` - mirror of `ffmpeg_runner.py`
- **Independent `AutoEditorApi` class** (NOT extending FFmpegApi)
- Settings page gets new "Auto-Editor Path" field (mirroring FFmpeg setup)
- Auto-editor jobs flow through the existing TaskQueue system
- **v1 only supports audio/motion edit methods**; subtitle hidden until pattern param UI added
- **v1 only "Add to Queue" button**; "Run Now" removed to avoid confusion about queue semantics

---

## 2. Frontend Page Design

**New page:** `frontend/src/pages/AutoCutPage.vue`

**Page structure:**
```
AutoCutPage.vue
├── FileDropInput (drag-drop single video/audio file)  # P1-5: single file only, reject multiple
├── BasicTab.vue
│   ├── Edit method selector (audio/motion)  # subtitle hidden in v1 (needs pattern param)
│   ├── Audio threshold slider (0.01-0.20)  # for audio edit method (P2: separate from motion)
│   ├── Motion threshold slider (0.01-0.20)  # for motion edit method (P2: separate from audio)
│   ├── When-silent action (cut / speed:X / volume:X / nil)
│   ├── When-normal action (nil / cut / speed:X / volume:X)  # P1-1: added cut for reverse editing
│   ├── Margin input (default 0.2s)
│   └── Smooth input (mincut/minclip)
├── AdvancedTab.vue
│   ├── Actions section
│   │   ├── Cut-out ranges (--cut-out)
│   │   ├── Add-in ranges (--add-in)
│   │   └── Set-action custom ranges
│   ├── Timeline section
│   │   ├── Frame rate override
│   │   ├── Sample rate override
│   │   └── Resolution override
│   ├── Container section
│   │   ├── Toggle: -vn / -an / -sn / -dn  # P2: validate not all disabled
│   │   ├── Faststart toggle (default ON, no flag when ON)  # P2: only output --no-faststart when OFF
│   │   └── Fragmented toggle (default OFF, only output when ON)  # P2: only output --fragmented when ON
│   ├── Video rendering
│   │   ├── Codec select (from auto-editor info -encoders video)  # Fixed: single-dash
│   │   ├── Video bitrate input
│   │   └── CRF input
│   ├── Audio rendering
│   │   ├── Codec select (from auto-editor info -encoders audio)  # Fixed: single-dash
│   │   ├── Audio bitrate input
│   │   ├── Audio layout
│   │   └── Audio normalize (peak/ebu)
│   └── Misc: --no-cache, --open (P1-10: warn user if enabled in queue mode), output extension (mp4/mkv/mov)
├── CommandPreview.vue (reused from config/, type='auto-editor')
└── Action buttons (Add to Queue)  # "Run Now" removed in v1
```

**CommandPreview XSS Prevention (P2):**
- Display user file paths as plain text ONLY (no `v-html` directive)
- Path content could contain HTML entities that cause XSS if rendered as HTML
- Use `{{ }}` text interpolation or `v-text` directive for safety

**Single File Constraint (P1-5):**
- FileDropInput MUST reject multiple files (v1 does not support batch processing)
- Backend `add_auto_editor_task()` also validates single file input
- If multiple files dropped: show error "Please select only one file"

**--open Warning (P1-10):**
- `--open` in queue workflow may launch system player from background thread (unexpected)
- v1 recommendation: Hide --open by default in UI, or show warning: "Output file will open automatically after processing"
- If implemented: add user confirmation or clear warning text

**Composables:**
- `useAutoEditor.ts` - mirrors `useCommandPreview` pattern:
  - `editMethod`, `audioThreshold` (for audio), `motionThreshold` (for motion)  # P2: split threshold by edit method
  - `whenSilentAction`, `whenNormalAction` (supports cut/speed/volume/nil)
  - `advancedOptions` (reactive object for all advanced params)
  - `commandPreview` (computed, builds preview via backend call)
  - `runAutoEditor()` - calls backend to queue the job

**Router:** Add `/auto-cut` route in `router.ts`, add nav item in `AppNavbar.vue`.

**Frontend State & Error Handling:**
- `useAutoEditor.ts` tracks auto-editor availability (path set, version compatible)
- Display status bar above BasicTab when auto-editor is unavailable (path not set, version invalid)
- Disable "Add to Queue" button when auto-editor is not configured/validated
- Show guidance to set path in Settings page

**Component Compatibility:**
- **Final decision**: Extend existing `CommandPreview.vue` with `type` prop
- Prop definition: `type: { type: String, default: 'ffmpeg', validator: (v) => ['ffmpeg', 'auto-editor'].includes(v) }`
- When `type='auto-editor'`: disable ffmpeg-specific highlighting, use generic command display
- If complexity grows, split to `AutoEditorCommandPreview.vue` in future

**Parameter Validation:**
- All UI options (Basic/Advanced tabs) must be verified against auto-editor v30.1.4 CLI manual
- Explicit mapping logic in `auto_editor_command_builder.py`, with unit tests for parameter combinations

**Verified Parameters (v30.1.4, dash-form only - underscores NOT accepted since v30.0.0):**
- Basic Tab: `--edit` (audio/motion; subtitle requires --edit "subtitle:pattern" with pattern param)
  - audio: `--edit audio:0.04` or `--edit audio:0.04,stream=0`
  - motion: `--edit motion:0.02` or `--edit motion:0.02,stream=0,blur=9,width=400`
  - subtitle (v2+): `--edit "subtitle:pattern,stream=0,ignore-case=false,max-count=nil"`
- Basic Tab: `--margin` (default 0.2s), `--smooth` (default 0.2s,0.1s)
- Basic Tab: `--when-silent` (cut/speed:X.X/volume:X.X/nil), `--when-normal` (nil/cut/speed:X.X/volume:X.X)
- Advanced Tab - Actions: `--cut-out`, `--add-in`, `--set-action`
- Advanced Tab - Timeline: `--frame-rate`, `--sample-rate`, `--resolution`
- Advanced Tab - Container: `-vn`, `-an`, `-sn`, `-dn`, `--faststart`, `--no-faststart`, `--fragmented`, `--no-fragmented`
- Advanced Tab - Video: `--video-codec` (query via `auto-editor info -encoders <format>`), `-b:v`, `-crf`
- Advanced Tab - Audio: `--audio-codec` (aac/fdk_aac/aac_at - query via `auto-editor info -encoders <format>`), `-b:a`, `--audio-layout`, `--audio-normalize` (peak/ebu)
- Advanced Tab - Misc: `--no-cache`, `--open`
- **Output format**: Controlled by `--output` file extension (e.g., `.mp4`, `.mkv`, `.mov`); `--output-format` is for yt-dlp only, NOT for local media
- **Audio output strategy (P2)**: Input `.mp3/.wav/.m4a` are audio-only; v1 output limited to mp4/mkv/mov containers. Consider adding `.mp3/.wav/.m4a` output for audio-only scenes in future.

**Encoder Discovery:**
- Use `auto-editor info -encoders <format>` (single dash, requires format parameter: mp4/mkv/mov)
- UI should populate codec dropdowns dynamically from encoder query, not hardcoded lists
- Mark unavailable encoders as "Not available" in UI
- Backend parses stdout into structured `{video: [], audio: [], subtitle: [], other: []}` based on `v: / a: / s: / other:` prefixes
- Cache encoder results by format: `encodersByFormat.mp4`, `encodersByFormat.mkv`, etc.

---

## 3. Backend Design

**New file:** `core/auto_editor_runner.py`

Mirrors `ffmpeg_runner.py` pattern:
```python
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

def validate_local_input(input_file: str) -> Path:
    """Validate input is a local file (NOT URL), exists, has supported extension.

    auto-editor 30.1.4 will download URLs via yt-dlp, which is out of scope for v1.
    """
    # Reject URL inputs
    p = urlparse(input_file)
    if p.scheme in ('http', 'https', 'ftp'):
        raise ValueError('URL input is not supported in v1. Use local file paths only.')

    # Resolve and validate local path
    path = Path(input_file).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f'input_file must be an existing local file: {input_file}')

    # Validate extension
    allowed_exts = {'.mp4', '.mov', '.mkv', '.m4v', '.mp3', '.wav', '.m4a', '.aac'}
    if path.suffix.lower() not in allowed_exts:
        raise ValueError(f'Unsupported media file extension: {path.suffix}. Allowed: {allowed_exts}')

    return path
```

class AutoEditorRunner:

**Command builder:** `core/auto_editor_command_builder.py`

**Note on Command Building:**
- `add_auto_editor_task()` validates params and saves structured data to queue (NOT build command)
- `task_runner` builds command ONCE when executing, saves argv + output_path to task metadata
- Preview uses `preview_auto_editor_command()` which builds independently for display
- DO NOT build command in both API and runner - choose one place only.
- Maps UI params to CLI args
- Handles Basic vs Advanced tier options
- Validates parameter combinations
- **Multi-range flags (P1-5)**: Repeat flag per range, e.g., `--cut-out 0,10 --cut-out 15,20` NOT `--cut-out 0,10 15,20`

### Stream Parser Design (P0-3)

Shared `task_runner.py` must handle both auto-editor (`\r` delimited) and FFmpeg (`\n` delimited) progress output.

**Design:** Per-task-type stream parser dispatch

```python
def read_process_output(proc, task_type):
    """Read process output with appropriate delimiter based on task type.

    Args:
        proc: subprocess.Popen process with stdout=PIPE, stderr=STDOUT
        task_type: 'auto_editor' or 'ffmpeg'

    Yields:
        Parsed progress dict or log line for each complete segment
    """
    if task_type == 'auto_editor':
        yield from _read_auto_editor_output(proc)
    else:  # ffmpeg (and others)
        yield from _read_ffmpeg_output(proc)

def _read_auto_editor_output(proc):
    """Read auto-editor output, delimited by \\r (machine progress mode)."""
    buffer = ''
    while True:
        chunk = proc.stdout.read(1)  # Read byte by byte for \r detection
        if not chunk:
            if buffer:
                yield _parse_auto_editor_segment(buffer)
            break
        buffer += chunk.decode('utf-8', errors='replace')
        if '\r' in buffer:
            segments = buffer.split('\r')
            # Last segment might be incomplete (no \r yet), keep in buffer
            for seg in segments[:-1]:
                if seg.strip():
                    yield _parse_auto_editor_segment(seg)
            buffer = segments[-1]
    proc.wait()

def _read_ffmpeg_output(proc):
    """Read FFmpeg output, delimited by \\n (log lines)."""
    for line in proc.stdout:
        line = line.decode('utf-8', errors='replace').rstrip('\n')
        if line.strip():
            yield _parse_ffmpeg_line(line)
    proc.wait()

def _parse_auto_editor_segment(segment):
    """Parse auto-editor --progress machine segment: title~current~total~eta_seconds\\r"""
    # Handle potential remaining \r or \n in segment
    segment = segment.strip().strip('\r').strip('\n')
    if not segment:
        return None
    parts = segment.split('~')
    if len(parts) >= 4:
        try:
            return {
                'title': parts[0],
                'current': int(parts[1]),
                'total': int(parts[2]),
                'progress': round(int(parts[1]) / int(parts[2]) * 100, 2) if int(parts[2]) > 0 else 0,
                'eta_seconds': float(parts[3]) if parts[3] not in ('', 'unknown') else None,
            }
        except (ValueError, IndexError):
            pass
    # If not machine format, treat as log line
    return {'type': 'log', 'message': segment}

def _parse_ffmpeg_line(line):
    """Parse FFmpeg log line for progress info."""
    # FFmpeg progress parsing logic (existing)
    return {'type': 'log', 'message': line}
```

**Key points:**
- Auto-editor: reads byte-by-byte, splits on `\r`, parses `title~current~total~eta_seconds` format
- FFmpeg: reads line-by-line (existing behavior), splits on `\n`
- Both modes merge stderr into stdout (`stderr=STDOUT`) to prevent deadlock
- Use `NO_COLOR=1` env var to prevent color codes in output (P1-7)

### Cancel Task Implementation Contract (P1-8)

```python
class AutoEditorRunner:
    def __init__(self):
        self.current_proc = None  # Store Popen handle for cancel

    def run_auto_editor(self, task_data):
        """Execute auto-editor command with cancel support."""
        command = build_command(...)
        self.current_proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            env={**os.environ, "NO_COLOR": "1"}
        )
        # Store proc in task metadata for cancel access
        task_data['proc'] = self.current_proc
        task_data['pid'] = self.current_proc.pid

        try:
            # Read output via stream parser (see above)
            for progress in read_process_output(self.current_proc, 'auto_editor'):
                if task_data.get('cancelled'):
                    break
                # Emit progress...
        finally:
            if self.current_proc:
                self.current_proc.wait()

    def cancel_task(self, task_data):
        """Cancel running task with graceful terminate then force kill."""
        proc = task_data.get('proc')
        if not proc:
            return {'success': False, 'error': 'No process to cancel'}

        output_path = task_data.get('output_path')
        try:
            # Step 1: Terminate (SIGTERM on Unix, CTRL_BREAK_EVENT on Windows)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Step 2: Force kill if terminate didn't work
                proc.kill()
                proc.wait(timeout=5)
        except Exception as e:
            return {'success': False, 'error': f'Cancel failed: {str(e)}'}
        finally:
            # Cleanup partial output file
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except OSError:
                    pass  # File might be locked
            return {'success': True, 'data': {'status': 'cancelled'}}
```

**Cancel workflow:**
1. Frontend emits `cancel_task` event with `task_id`
2. Backend sets `task_data['cancelled'] = True`
3. `cancel_task()` calls `terminate()` first, then `kill()` after timeout
4. Process group killed on Unix (`os.killpg`) for child processes
5. Partial output file cleaned up
6. Task status set to `'cancelled'`

### Output Directory Atomic Validation (P1-9)

```python
def generate_output_path(input_file: str, output_dir: str, task_id: str, extension: str) -> Path:
    """Generate unique output path with atomic validation.

    - Ensures output_dir exists and is writable
    - Validates final path is within output_dir (prevent path traversal)
    - Uses task_id for uniqueness (prevents overwrite)
    """
    output_dir = Path(output_dir).expanduser().resolve()
    input_path = Path(input_file).expanduser().resolve()

    # 1. Validate output_dir exists and is writable
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    if not os.access(output_dir, os.W_OK):
        raise PermissionError(f'Output directory not writable: {output_dir}')

    # 2. Generate unique filename based on task_id
    stem = input_path.stem
    filename = f'{stem}_{task_id[:8]}.{extension.lstrip(".")}'
    output_path = output_dir / filename

    # 3. Prevent path traversal: ensure output_path is within output_dir
    output_path = output_path.resolve()
    if not str(output_path).startswith(str(output_dir)):
        raise ValueError(f'Invalid output path: path traversal detected')

    # 4. Check for unexpected overwrite (should not happen with task_id)
    if output_path.exists():
        # Very unlikely with task_id, but be safe
        raise FileExistsError(f'Output path already exists: {output_path}')

    return output_path
```

**Backend API Design (Final):**

**Independent `AutoEditorApi` class** (Recommended, decoupled from FFmpeg)

All API methods return unified `ApiResult` format:
```python
# ApiResult format (all methods):
# Success: {'success': True, 'data': ...}
# Failure: {'success': False, 'error': '...'}
```

```python
class AutoEditorApi(Bridge):
    def __init__(self, settings_manager):
        self.settings = settings_manager  # Injected settings manager for persistence
        
    @expose
    def set_auto_editor_path(self, path: str) -> dict:
        """Validate binary by running --version, check return code, save to settings"""
        try:
            result = subprocess.run(
                [path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode !=0:
                return {'success': False, 'error': f'Binary validation failed: {result.stderr}'}
            # Save valid path to settings via settings_manager
            self.settings.set('auto_editor_path', path)
            return {'success': True, 'data': {'version': result.stdout.strip()}}
        except Exception as e:
            return {'success': False, 'error': f'Path validation failed: {str(e)}'}
        
    # Version compatibility: support 30.1.x (30.1.0+ has -encoders, -crf; 30.0.0+ removed underscore flags)
    SUPPORTED_VERSION_RANGE = ">=30.1.0,<31.0.0"

    @expose
    def get_auto_editor_status(self) -> dict:
        """Check auto-editor availability and version compatibility"""
        path = self.settings.get('auto_editor_path')
        if not path:
            return {'success': False, 'error': 'auto-editor path not configured'}
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=10,
                                   env={**os.environ, "NO_COLOR": "1"})
            if result.returncode != 0:
                return {'success': False, 'error': result.stderr.strip() or result.stdout.strip()}

            version_str = result.stdout.strip()
            # Parse version: expect "auto-editor 30.1.4" or "30.1.4"
            import re
            match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
            if not match:
                return {'success': False, 'error': f'Cannot parse version: {version_str}'}

            major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

            # Check supported range: >=30.1.0, <31.0.0
            compatible = (major == 30 and minor >= 1) or (major == 30 and minor == 0 and patch >= 0)
            # More precise: >=30.1.0,<31.0.0
            compatible = (major == 30 and minor >= 1) or (major == 30 and minor == 0 and patch >= 0)
            # Actually, let me be more explicit:
            version_tuple = (major, minor, patch)
            min_version = (30, 1, 0)
            max_version = (31, 0, 0)
            compatible = min_version <= version_tuple < max_version

            status_data = {
                'path': path,
                'version': version_str,
                'version_tuple': [major, minor, patch],
                'available': True,
                'compatible': compatible,
            }
            if not compatible:
                status_data['warning'] = f'Version {version_str} may not be fully compatible. Supported: {self.SUPPORTED_VERSION_RANGE}'

            return {'success': True, 'data': status_data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
    @expose
    def get_auto_editor_encoders(self, output_format: str = "mp4") -> dict:
        """Query available encoders via `auto-editor info -encoders <format>` (single dash, requires format param)

        Args:
            output_format: Output container format (mp4/mkv/mov), dots stripped automatically.
                Determines which encoders are available for the target output format.

        Returns:
            {'success': True, 'data': {'video': [...], 'audio': [...], 'subtitle': [...], 'other': [...]}}
        """
        allowed = {"mp4", "mkv", "mov"}
        fmt = output_format.lower().lstrip(".")
        if fmt not in allowed:
            return {'success': False, 'error': f'Unsupported output format: {output_format}. Allowed: {allowed}'}

        path = self.settings.get('auto_editor_path')
        if not path:
            return {'success': False, 'error': 'auto-editor path not configured'}
        try:
            # Use single-dash -encoders (NOT --encoders), requires format parameter
            result = subprocess.run(
                [path, 'info', '-encoders', fmt],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                env={**os.environ, "NO_COLOR": "1"},
            )
            if result.returncode == 0:
                return {'success': True, 'data': self._parse_encoder_output(result.stdout)}
            return {'success': False, 'error': result.stderr.strip() or result.stdout.strip()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _parse_encoder_output(self, stdout: str) -> dict:
        """Parse `auto-editor info -encoders <fmt>` output into structured dict.

        Output format: lines with prefixes 'v: ', 'a: ', 's: ', 'other: '
        """
        import re
        result = {'video': [], 'audio': [], 'subtitle': [], 'other': []}
        # Parse section by section
        section_map = {'v:': 'video', 'a:': 'audio', 's:': 'subtitle', 'other:': 'other'}
        current_section = None
        for line in stdout.splitlines():
            line = line.strip()
            for prefix, key in section_map.items():
                if line.startswith(prefix):
                    current_section = key
                    # Extract encoder names from the rest of the line
                    encoders_part = line[len(prefix):].strip()
                    result[key] = [e.strip() for e in encoders_part.split() if e.strip()]
                    break
        return result
        
    @expose
    @expose
    def add_auto_editor_task(self, input_file: str, params: dict) -> dict:
        """Validate params and enqueue task. NO command building here (P0-2).

        Command is built once by task_runner at execution time.

        Returns: {'success': True, 'data': {'task_id': '...'}}
        """
        # 1. Validate input_file (URL rejection, file exists, extension check)
        try:
            validated_path = validate_local_input(input_file)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

        # 2. Validate params (edit method, thresholds, flag combinations)
        # TODO: call auto_editor_command_builder.validate_params(params)

        # 3. Check audio-only file + motion edit incompatibility (P1-6)
        if params.get('edit_method') == 'motion' and validated_path.suffix.lower() in {'.mp3', '.wav', '.m4a', '.aac'}:
            return {'success': False, 'error': 'Motion edit requires video stream; input is audio-only'}

        # 4. Enqueue structured task data (NO command building)
        import uuid
        task_id = str(uuid.uuid4())
        output_dir = self.settings.get('auto_editor_output_dir', './data/auto_editor_output')
        task_data = {
            'type': 'auto_editor',
            'task_id': task_id,
            'input_file': str(validated_path),
            'params': params,
            'output_dir': output_dir,
            # Command will be built by task_runner at execution time
        }
        # task_queue.add(task_data)  # Pseudo: add to queue
        return {'success': True, 'data': {'task_id': task_id}}

    @expose
    def preview_auto_editor_command(self, params: dict) -> dict:
        """Expose command preview interface.

        Frontend MUST pass params with 'input_file' key (P1-4: no 'input' alias).
        Preview builds independently; does NOT generate final unique output path.

        Returns {argv: list[str], display: str}
        """
        input_file = params.get('input_file')  # P1: Remove 'input' alias fallback
        if not input_file:
            return {'success': False, 'error': 'input_file is required for preview'}
        # Preview uses placeholder output path (not final task output path)
        preview_params = {**params, '_preview_mode': True}
        command = auto_editor_command_builder.build_command(input_file, preview_params)
        # For display: use platform-appropriate formatting
        import os, shlex
        if os.name == 'nt':
            import subprocess
            display = subprocess.list2cmdline(command)  # Windows-safe
        else:
            display = shlex.join(command)  # POSIX-safe
        return {'success': True, 'data': {'argv': command, 'display': display}}
```

**Note:** Removed `get_auto_editor_version()` - merged into `get_auto_editor_status()`.

**Output parsing:** auto-editor uses `--progress machine` format (title~current~total~eta\r). Parse from merged stdout (stderr redirected to stdout). Key difference: auto-editor uses `\r` for line refresh, NOT `\n`.

**Settings integration:** Add `auto_editor_path` to the settings model (mirroring `ffmpeg_path`).

**Persistence mechanism:**
- Uses existing `settings_manager` (or `Settings` class) for read/write operations
- Read: `settings_manager.get('auto_editor_path')` returns stored path or None
- Write: `settings_manager.set('auto_editor_path', path)` saves after validation
- Settings stored in JSON file (e.g., `config/settings.json`) or database, consistent with existing ffmpeg_path storage
- On app startup: read path, validate if exists, update frontend availability state

---

## 4. Data Flow

**Complete flow for running an auto-editor job:**

> **Command building ownership (P0-2):** API only validates/enqueues params. Runner builds command ONCE at execution time. Preview builds independently (no final output path).

```
1. User drops file in AutoCutPage (single file only)
   └─ FileDropInput validates: single file, local path, supported extension
   └─ Reject URLs and multiple files

2. User configures options (Basic tab or Advanced tab)
   └─ UI state updates reactive refs in useAutoEditor.ts
   └─ BasicTab: when-normal now includes 'cut' option (reverse editing scenario)

3. User clicks "Add to Queue"
   └─ useAutoEditor.runAutoEditor()
       └─ call('add_auto_editor_task', inputFile, params)

4. Backend: AutoEditorApi.add_auto_editor_task()
   └─ Validate input_file: reject URLs (http/https/ftp), check file exists, validate extension
   └─ Validate params: check edit method, thresholds, flag combinations
   └─ Enqueue structured task data to task_queue (NO command building here)
       └─ Task data: {type: 'auto_editor', input_file, params, task_id, output_dir}
       └─ Does NOT build command, does NOT generate output path
       └─ Returns: {'success': True, 'data': {'task_id': '...'}}

5. Task picked up by task_runner.py from thread pool
   └─ Build command ONCE: command = build_command(input_file, params, task_id)
       └─ build_command() adds --progress machine, generates unique --output path
       └─ Save argv + output_path to task metadata (for progress/cancel operations)
       └─ proc = subprocess.Popen(command, stdout=PIPE, stderr=STDOUT, shell=False,
                                   env={**os.environ, "NO_COLOR": "1"})
           ├─ task_runner reads proc.stdout by CHUNK (NOT for line in proc.stdout)
           ├─ Stream parser: support both \r (auto-editor) and \n (ffmpeg) delimiters
           ├─ For auto-editor: maintain buffer, split by \r to get segments
           ├─ parse_output(segment) → extract progress from --progress machine format
           ├─ queue.emit('task_progress', {task_id, progress, eta_seconds})
           ├─ On process end: check proc.returncode
           └─ queue.emit('task_complete', {task_id, output_path, status, error?})

6. Frontend receives events via useTaskProgress
   └─ TaskProgressBar / TaskLogPanel update (reused components)

7. Output file saved to configured output directory
   └─ Unique filename prevents overwrite (task_id-based, validated against output_dir)
   └─ On cancel: terminate process, cleanup partial output file
```

**Command preview flow** (realtime, no task created):
> **Note:** Preview builds independently and does NOT generate final unique output path.
> **P2:** Preview command MUST use the real configured binary path from settings, so users see the exact command that will execute.

```
useAutoEditor.ts → Build params with 'input_file' key explicitly
→ call('preview_auto_editor_command', { input_file: selectedFile, ...otherOptions })
→ AutoEditorApi.preview_auto_editor_command()
→ auto_editor_command_builder.build_command(input_file, params) → returns command list
→ Preview command uses configured auto_editor_path (NOT placeholder)
→ Preview output path is placeholder (e.g., '/preview/output.mp4')
→ Returns {argv: command_list, display: ' '.join(command_list)}
→ CommandPreview.vue displays it with type='auto-editor' prop (plain text, no v-html)
```

---

## 5. Integration Points

### Settings Page
- Add "Auto-Editor Path" input field (same pattern as FFmpeg Setup)
- Validate binary on path change
- Store in settings model

### AppNavbar
- Add nav item for Auto Cut page between existing items
- Use appropriate icon (e.g., scissors/cut symbol)

### Router (`frontend/src/router.ts`)
- Add route: `{ path: '/auto-cut', component: () => import('./pages/AutoCutPage.vue') }`

### TaskQueue System
- Reuse existing `task_runner.py` thread pool
- Reuse `TaskQueue` state management
- Reuse `TaskProgressBar`, `TaskLogPanel` components
- New task type: `{ type: 'auto_editor', input_file, params }`

---

## 6. Dependencies

- **auto-editor binary** (Required, user-provided, configured in Settings)
  - Download source: https://github.com/WyattBlue/auto-editor/releases/tag/30.1.4
  - **Security note**: Manual configuration is the **primary and recommended** method.
  - **Optional auto-downloader** (if implemented in future):
    - **MUST** verify SHA256 checksum against **hardcoded expected values** in source code (e.g., `EXPECTED_CHECKSUMS = {'v30.1.4-win.exe': 'abc123...', 'v30.1.4-macos': 'def456...'}`)
    - Checksum values must be obtained from **official GitHub release page** and hardcoded by developers
    - **DO NOT** scrape checksums from the same download page (risk of simultaneous compromise)
    - Inform users of supply chain risks before downloading
    - Allow users to cancel and choose manual configuration
    - **Recommendation**: Move auto-downloader to "Future Enhancements" to avoid initial complexity and security burden.
- **ffmpeg**: auto-editor bundles/uses its own ffmpeg; **DO NOT** inject external ffmpeg path (--ffmpeg-location does NOT exist in v30.1.4). Verify available encoders via `auto-editor info -encoders <format>`.
- No new npm packages required
- No new Python packages required (auto-editor is a separate binary)
- Reuses: pywebvue, task_queue, composables pattern

**Removed from design:**
- `--ffmpeg-location` parameter (NOT in auto-editor v30.1.4 CLI)
- ffmpeg_path injection to auto-editor
- `get_auto_editor_version()` (merged into `get_auto_editor_status()`)

---

## 7. Out of Scope (Future Enhancements)

- URL download integration (yt-dlp)
- Timeline visualization of cuts
- Preview of edited output before saving
- Batch processing UI (multiple files with same settings)
- Auto-editor Python API integration (if available in future)
- **Binary auto-downloader with multi-platform support** (security-sensitive, manual configuration preferred for initial release)

---

## 8. Testing Strategy

### 8.1 Unit Tests (CI-Automatable, no binary required)
- `auto_editor_command_builder.build_command()`:
  - Test parameter mapping for all Basic/Advanced tab options
  - Test --output path generation (unique filename, configured dir, no overwrite)
  - Test invalid parameter handling
  - **Removed**: Test ffmpeg_path injection via --ffmpeg-location (NOT in v30.1.4)
  - Test DASH-form flags only (no underscores, v30.0.0+ compliance)
  - **P0-2**: Test parse_output with trailing \r: `"Video~123~1000~45.2\r"` → progress=12.3, eta_seconds=45.2
  - **P0-2**: Test parse_output with multiple \r segments: `"Video~1~100~99\rVideo~2~100~98\r"` → current=2
  - **P0-2**: Test title containing ~: `"foo~bar~2~10~8\r"` → title="foo~bar", progress=20.0
  - **P1-5**: Test multi-range flags: 2 --cut-out flags for 2 ranges, NOT space-separated
  - **P1-4**: Test URL rejection (http/https/ftp): `validate_local_input("https://...")` raises ValueError
  - **P1-6**: Test output extension from params: `params['output_extension']='mkv'` → suffix='.mkv'
  - **P1-1**: Test when-normal=cut passes through to builder correctly
  - **P1-6**: Test motion edit + audio-only file raises ValueError in add_auto_editor_task
  - **P1-9**: Test output path generation with task_id is within output_dir (path traversal check)
- `auto_editor_runner.parse_output()`:
  - Test `--progress machine` format: `"Video~123~1000~45.2\r"` → {progress: 12.3, eta_seconds: 45.2}  # Fixed: ETA is float seconds, NOT "00:45"
  - Test \r handling: chunk with multiple \r, extract last segment
  - Test error detection: `"Error! ..."` → {status: 'error', error: '...'}  # Fixed: prefix is "Error!" not "Error:"
  - Test returncode check: proc.returncode == 0 for success (not string matching)
  - Test NO_COLOR env var prevents color codes in output
- `auto_editor_runner.cancel_task()`:
  - Test terminate() then wait(timeout)
  - Test kill() on TimeoutExpired
  - Test partial output file cleanup after cancel
  - Test task status set to 'cancelled' after cancel
- `set_auto_editor_path()`:
  - Test valid path validation (mock subprocess.run, returns success + version)
  - Test invalid path (mock subprocess.run to raise exception)
  - Test incompatible version (29.x or 30.0.x) returns warning in data
- `get_auto_editor_status()`:
  - Test returns ApiResult format with version_tuple and compatible flag
  - Test path not configured: {'success': False, 'error': '...'}
  - Test 30.1.4 returns compatible=True
  - Test 29.0.0 returns compatible=False with warning
- `get_auto_editor_encoders()`:
  - Test returns structured output: {'video': [...], 'audio': [...], 'subtitle': [...], 'other': [...]}
  - Test default format 'mp4' when not specified
  - Test '.mp4' normalized to 'mp4'
  - Test invalid format returns error
  - Test uses `-encoders` (single dash) NOT `--encoders`
  - Test NO_COLOR env var set
- `preview_auto_editor_command()`:
  - Test returns ApiResult with 'argv' (list) and 'display' (string)
  - Test input_file missing: {'success': False, 'error': '...'}
  - Test does NOT accept 'input' alias (P1-4: only 'input_file')
  - Test preview command uses placeholder output path (not final task output)
- `generate_output_path()`:
  - Test output path is within output_dir (path traversal prevention)
  - Test task_id-based filename prevents overwrite
  - Test output_dir created if not exists
  - Test raises PermissionError if output_dir not writable

### 8.2 Integration Tests (Semi-Automated, requires mock or real binary)
- **Mock-based (CI-Automatable)**:
  - Frontend-backend: `preview_auto_editor_command` returns {argv: list, display: str}
  - Task queue: `add_auto_editor_task` creates task with structured params (NO command)
  - Task queue: `task_runner` builds command ONCE at execution time
  - Settings: `set_auto_editor_path` saves valid path via settings_manager.set()
  - **Removed**: FFmpeg dependency tests (no --ffmpeg-location in v30.1.4)
  - Verify --progress machine is added to command
  - Verify output path uses configured directory + unique name
  - Verify URL rejection in API, builder, and runner (P1-4: all layers)
  - Verify single file constraint: multiple files rejected by API
- **Real-binary (Manual/CI-with-binary)**:
  - Actual `set_auto_editor_path` with real auto-editor binary validates and returns version
  - `build_command` produces command that can be executed by real binary
  - Full task run: auto-editor processes sample video/audio file successfully
  - Verify --progress machine output is parseable (eta_seconds is float)
  - Verify stream parser handles both \r (auto-editor) and \n (ffmpeg) - regression test (P0-3)

### 8.3 E2E Tests (Manual Testing Guide)
- **Prerequisites**: auto-editor binary configured (ffmpeg bundled/in PATH)
- **Test 1**: Configure auto-editor path in Settings → verify status displays correctly (get_auto_editor_status)
- **Test 2**: Upload media file → configure basic options → add to queue → verify task completes, output file in configured dir
- **Test 3**: Test error cases: invalid path, unsupported media file
- **Test 4**: Verify CommandPreview updates in real-time when changing options (shows argv + display)
- **Test 5**: Test all Basic Tab actions (cut/speed:X/volume:X/nil) with sample file, including when-normal=cut
- **Test 6**: Test cancel task → verify process terminated, output file cleanup, task status='cancelled'
- **Test 7**: Verify subtitle edit method hidden in v1 (pattern param not yet implemented)
- **Test 8**: Test single file only: drop multiple files → verify error message (P1-5)
- **Test 9**: Test audio-only file + motion edit → verify error "Motion edit requires video stream" (P1-6)
- **Test 10**: Test --open in queue → verify warning displayed or feature hidden (P1-10)
- **Test 11**: Test URL input → verify rejected at frontend and backend (P1-4)
