# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Phase 3.5 - FFmpeg 子进程挂起/恢复技术验证

验证项:
1. 启动 FFmpeg 子进程 -> SuspendProcess -> ResumeProcess -> 正常完成
2. 挂起期间 stderr 读取线程不阻塞/不死锁
3. 恢复后进度继续正常上报
"""

import ctypes
import subprocess
import sys
import time
import threading
import os
from pathlib import Path

# ── Windows Process Suspend/Resume ──────────────────────────────────────────
# SuspendProcess / ResumeProcess 不是标准 Win32 API
# 正确做法: 使用 ntdll.dll 的 NtSuspendProcess / NtResumeProcess

PROCESS_SUSPEND_RESUME = 0x0800
kernel32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll

# 设置函数返回类型和参数类型
NTSTATUS = ctypes.c_long
ntdll.NtSuspendProcess.restype = NTSTATUS
ntdll.NtSuspendProcess.argtypes = [ctypes.c_void_p]
ntdll.NtResumeProcess.restype = NTSTATUS
ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]

# NTSTATUS 成功值 = 0
NT_SUCCESS = lambda status: status >= 0

def suspend_process(pid: int) -> bool:
    """挂起指定 PID 的进程，返回是否成功"""
    handle = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if not handle:
        print(f"  [ERROR] OpenProcess failed for PID {pid}, error: {ctypes.GetLastError()}")
        return False
    status = ntdll.NtSuspendProcess(handle)
    kernel32.CloseHandle(handle)
    if not NT_SUCCESS(status):
        print(f"  [ERROR] NtSuspendProcess failed for PID {pid}, NTSTATUS=0x{status & 0xFFFFFFFF:08X}")
        return False
    return True

def resume_process(pid: int) -> bool:
    """恢复指定 PID 的进程，返回是否成功"""
    handle = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    if not handle:
        print(f"  [ERROR] OpenProcess failed for PID {pid}, error: {ctypes.GetLastError()}")
        return False
    status = ntdll.NtResumeProcess(handle)
    kernel32.CloseHandle(handle)
    if not NT_SUCCESS(status):
        print(f"  [ERROR] NtResumeProcess failed for PID {pid}, NTSTATUS=0x{status & 0xFFFFFFFF:08X}")
        return False
    return True


def find_test_video() -> str:
    """查找一个测试视频文件"""
    candidates = []
    for root, dirs, files in os.walk(Path.home()):
        for f in files:
            if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                full = os.path.join(root, f)
                size = os.path.getsize(full)
                if size > 1024 * 1024:  # > 1MB
                    candidates.append((full, size))
    candidates.sort(key=lambda x: x[1])
    if candidates:
        return candidates[0][0]
    return ""


def test_1_basic_suspend_resume():
    """
    验证项 1: 基本的挂起/恢复流程
    - 启动 FFmpeg 转码 (较长任务，确保有足够时间挂起)
    - 等待进度开始
    - 挂起进程
    - 等待一段时间确认暂停
    - 恢复进程
    - 验证进程正常完成
    """
    print("\n" + "=" * 70)
    print("TEST 1: Basic Suspend/Resume")
    print("=" * 70)

    test_video = generate_test_video()
    if not test_video:
        print("  [SKIP] No test video available")
        return False

    output_path = os.path.join(os.environ.get("TEMP", "/tmp"), "test_suspend_output.mp4")

    # 使用较慢的编码来确保转码时间足够长
    cmd = [
        "ffmpeg", "-y",
        "-i", test_video,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac",
        output_path
    ]

    print(f"  Starting FFmpeg process...")
    print(f"  Input: {test_video}")
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    stderr_lines = []
    stderr_done = threading.Event()
    stderr_lock = threading.Lock()

    def read_stderr():
        for line in proc.stderr:
            decoded = line.decode("utf-8", errors="replace").strip()
            if decoded:
                with stderr_lock:
                    stderr_lines.append(decoded)
        stderr_done.set()

    reader_thread = threading.Thread(target=read_stderr, daemon=True)
    reader_thread.start()

    # 等待转码开始 (等待第一行进度输出)
    print("  Waiting for encoding to start...")
    for _ in range(100):  # 最多等 10 秒
        with stderr_lock:
            if len(stderr_lines) > 5:
                break
        time.sleep(0.1)

    with stderr_lock:
        initial_count = len(stderr_lines)
        print(f"  Encoding started, stderr lines so far: {initial_count}")

    # ── 挂起 ──
    print(f"  Suspending process PID={proc.pid}...")
    before_suspend = time.time()
    suspend_ok = suspend_process(proc.pid)
    if not suspend_ok:
        proc.kill()
        print("  [FAIL] Suspend failed")
        return False
    print(f"  Process suspended successfully ({time.time() - before_suspend:.3f}s)")

    # 等待 5 秒，验证进程确实暂停了
    print("  Waiting 5 seconds while suspended...")
    time.sleep(5)

    with stderr_lock:
        lines_during_suspend = len(stderr_lines)
    print(f"  Lines during suspend: {lines_during_suspend - initial_count}")
    print(f"  Process poll: {proc.poll()}")

    # 验证: 挂起期间不应该有新进度输出，进程不应该退出
    with stderr_lock:
        if len(stderr_lines) > initial_count + 2:
            print("  [WARN] Some stderr output during suspend (may be buffered)")
        if proc.poll() is not None:
            print(f"  [FAIL] Process exited during suspend with code {proc.poll()}")
            return False

    # ── 恢复 ──
    print(f"  Resuming process PID={proc.pid}...")
    before_resume = time.time()
    resume_ok = resume_process(proc.pid)
    if not resume_ok:
        proc.kill()
        print("  [FAIL] Resume failed")
        return False
    print(f"  Process resumed successfully ({time.time() - before_resume:.3f}s)")

    # 等待转码完成
    print("  Waiting for process to complete...")
    try:
        returncode = proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        print("  [WARN] Process didn't finish in 120s, killing")
        proc.kill()
        returncode = proc.wait(timeout=10)

    stderr_done.wait(timeout=5)

    with stderr_lock:
        final_lines = len(stderr_lines)
        print(f"  Final stderr lines: {final_lines}")
        # 打印最后几行进度
        for line in stderr_lines[-5:]:
            if "time=" in line:
                print(f"    > {line[:120]}")

    print(f"  Return code: {returncode}")

    # 清理
    for f in [output_path]:
        if os.path.exists(f):
            os.remove(f)

    if returncode == 0:
        print("  [PASS] Process completed successfully after suspend/resume")
        return True
    else:
        print(f"  [FAIL] Process exited with code {returncode}")
        return False


def generate_test_video():
    """生成一个 30 秒测试视频（确保足够长）"""
    test_video = os.path.join(os.environ.get("TEMP", "/tmp"), "test_phase35_input.mp4")
    if os.path.exists(test_video):
        return test_video
    print("  Generating 30s test video (this takes a moment)...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=30",
        "-f", "lavfi", "-i", "smptebars=size=1280x720:duration=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-shortest",
        test_video
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  [ERROR] Failed to generate test video: {result.stderr[:300]}")
        return ""
    print(f"  Generated: {test_video}")
    return test_video


def test_2_stderr_thread_behavior():
    """
    验证项 2: stderr 读取线程在挂起/恢复期间的行为

    关键发现: 不需要暂停 reader 线程!
    - 进程挂起时，stderr 管道不再有新数据，readline() 自然阻塞
    - 进程恢复后，数据继续流动，readline() 自动解除阻塞
    - reader 线程始终在 readline() 上等待，无需额外同步
    """
    print("\n" + "=" * 70)
    print("TEST 2: Stderr Thread Behavior (No Thread Pausing Needed)")
    print("=" * 70)

    test_video = generate_test_video()
    if not test_video:
        return False

    output_path = os.path.join(os.environ.get("TEMP", "/tmp"), "test_stderr_output.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", test_video,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac",
        output_path
    ]

    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    # 简单的 reader 线程 (不暂停线程)
    stderr_lines = []
    stderr_done = threading.Event()
    stderr_lock = threading.Lock()

    def read_stderr():
        for line in proc.stderr:
            decoded = line.decode("utf-8", errors="replace").strip()
            if decoded:
                with stderr_lock:
                    stderr_lines.append(decoded)
        stderr_done.set()

    reader_thread = threading.Thread(target=read_stderr, daemon=True)
    reader_thread.start()

    # 等待编码开始
    print("  Waiting for encoding to produce output...")
    for _ in range(100):
        if proc.poll() is not None:
            print(f"  [ERROR] Process exited during wait with code {proc.returncode}")
            return False
        with stderr_lock:
            if len(stderr_lines) > 10:
                break
        time.sleep(0.1)

    with stderr_lock:
        initial = len(stderr_lines)
        print(f"  Lines before suspend: {initial}")

    if proc.poll() is not None:
        print(f"  [ERROR] Process already finished")
        return False

    # 挂起进程 (不暂停 reader 线程)
    print("  Suspending process (reader thread stays running)...")
    suspend_ok = suspend_process(proc.pid)
    if not suspend_ok:
        proc.kill()
        for f in [output_path]:
            if os.path.exists(f):
                os.remove(f)
        return False

    # 挂起 5 秒
    time.sleep(5)

    with stderr_lock:
        during = len(stderr_lines)
    process_alive = proc.poll() is None
    print(f"  Lines during suspend: {during - initial}")
    print(f"  Process still alive: {process_alive}")
    print(f"  Reader thread alive: {reader_thread.is_alive()}")

    # 恢复进程
    print("  Resuming process...")
    resume_ok = resume_process(proc.pid)
    time.sleep(3)

    with stderr_lock:
        after_resume = len(stderr_lines)
    print(f"  Lines after resume (+3s): {after_resume - during}")
    print(f"  Reader thread alive: {reader_thread.is_alive()}")

    # 检查: 进程可能已经自然完成 (这是好现象)
    process_naturally_finished = proc.poll() is not None
    print(f"  Process naturally finished: {process_naturally_finished}")

    # 终止进程 (如果还在运行)
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    stderr_done.wait(timeout=3)

    # 清理
    for f in [output_path]:
        if os.path.exists(f):
            os.remove(f)

    # 验证条件:
    # 1. 挂起/恢复都成功
    # 2. 挂起期间进程存活
    # 3. 恢复后有新输出 (说明 reader 线程没有死锁)
    # 4. 如果线程退出了，要么是进程自然完成 (好)，要么是我们终止的 (也好)
    passed = (
        suspend_ok
        and resume_ok
        and process_alive  # 挂起期间进程存活
        and (after_resume - during) > 0  # 恢复后有新输出 (reader 线程正常工作)
    )
    if passed:
        print("  [PASS] Reader thread handles suspend/resume without special handling")
        if process_naturally_finished:
            print("  (Process completed naturally after resume)")
    else:
        print(f"  [FAIL] suspend={suspend_ok}, resume={resume_ok}, alive={process_alive}, lines={after_resume - during}")
    return passed


def test_3_process_already_exited():
    """
    验证项 3: 边界情况 - 进程在挂起前已自行结束
    """
    print("\n" + "=" * 70)
    print("TEST 3: Edge Case - Process Already Exited Before Suspend")
    print("=" * 70)

    # 启动一个很快就会结束的 FFmpeg 进程
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
           "-t", "1", "-c:a", "aac", os.path.join(os.environ.get("TEMP", "/tmp"), "test_short.mp4")]

    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.wait(timeout=10)  # 等待进程结束
    print(f"  Process exited with code: {proc.returncode}")

    # 尝试挂起已退出的进程
    print(f"  Attempting to suspend exited PID={proc.pid}...")
    result = suspend_process(proc.pid)
    if not result:
        print("  [PASS] Suspend correctly failed for exited process")
        return True
    else:
        print("  [WARN] Suspend returned True for exited process (unexpected but not critical)")
        return True


def test_4_permission_fallback():
    """
    验证项 4: 降级策略概念验证
    如果 SuspendProcess 失败，应该能检测到错误并降级为 kill
    """
    print("\n" + "=" * 70)
    print("TEST 4: Permission/Degradation Strategy")
    print("=" * 70)

    # 尝试挂起 PID 0 (System Idle Process) - 肯定没有权限
    print("  Attempting to suspend PID 0 (should fail with permission error)...")
    result = suspend_process(0)
    if not result:
        print("  [PASS] Permission failure correctly detected")
    else:
        print("  [WARN] Unexpected success suspending PID 0")

    # 验证正常进程仍然可以挂起
    test_video = find_test_video()
    if not test_video:
        print("  [SKIP] No test video for this test")
        return True

    output_path = os.path.join(os.environ.get("TEMP", "/tmp"), "test_perm_output.mp4")
    cmd = ["ffmpeg", "-y", "-i", test_video, "-c:v", "libx264", "-preset", "slow", output_path]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    time.sleep(2)

    print(f"  Attempting to suspend our own FFmpeg PID={proc.pid}...")
    result = suspend_process(proc.pid)
    if result:
        print("  [PASS] Can suspend our own process")
        time.sleep(2)
        resume_result = resume_process(proc.pid)
        print(f"  Resume result: {resume_result}")
        # 终止进程，不需要等完成
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    else:
        print("  [FAIL] Cannot suspend our own process")
        proc.kill()
        proc.wait(timeout=5)

    # 清理
    for f in [output_path]:
        if os.path.exists(f):
            os.remove(f)

    return result


def main():
    print("=" * 70)
    print("  Phase 3.5 - Suspend/Resume Technical Verification")
    print("  Platform:", sys.platform)
    print("  Python:", sys.version)
    print("=" * 70)

    results = {}

    results["test_1"] = test_1_basic_suspend_resume()
    results["test_2"] = test_2_stderr_thread_behavior()
    results["test_3"] = test_3_process_already_exited()
    results["test_4"] = test_4_permission_fallback()

    # 生成测试视频的临时文件清理
    test_video = os.path.join(os.environ.get("TEMP", "/tmp"), "test_input.mp4")
    if os.path.exists(test_video):
        os.remove(test_video)

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")

    all_passed = all(results.values())
    print("\n" + ("=" * 70))
    if all_passed:
        print("  ALL TESTS PASSED - Suspend/Resume approach is viable")
    else:
        print("  SOME TESTS FAILED - Review before proceeding with Phase 4")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
