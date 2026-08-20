# -*- coding: utf-8 -*-
"""自动收尾：等合成完成 → mp3 转换 → 同步 electron → 打包 → 更新安装版"""
import os, subprocess, sys, time, shutil

LOG = r"D:\tts_scripts\autofinish.log"
def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
    return r.returncode == 0, (r.stdout + r.stderr)[-800:]

VOICE = r"D:\tts_voice"
EXPECTED = 365

# 1. 等合成完成（最多 12 小时）
log("等待合成完成…")
while True:
    total = 0
    for root, _, files in os.walk(VOICE):
        total += sum(1 for f in files if f.endswith(".wav") and os.path.getsize(os.path.join(root, f)) > 1000)
    if total >= EXPECTED:
        log(f"合成完成：{total} 个文件")
        break
    if "全部完成" in open(r"D:\tts_scripts\loop.log", encoding="utf-8", errors="ignore").read():
        log(f"loop 标记完成（文件 {total} 个）")
        break
    time.sleep(120)

# 2. wav → mp3
log("开始 wav→mp3 转换…")
ok, out = sh(r"python C:\Users\windows\ZCodeProject\ai-galgame\tools\wav2mp3_voice.py")
log(f"mp3 转换: {'OK' if ok else 'FAIL'} {out[-200:]}")

# 3. 同步 electron
log("同步 electron/game…")
ok, out = sh(r"python C:\Users\windows\ZCodeProject\ai-galgame\tools\sync_electron.py")
log(f"同步: {'OK' if ok else 'FAIL'} {out[-200:]}")

# 4. 打包
log("开始打包（npm run dist）…")
ok, out = sh(r"cd /d C:\Users\windows\ZCodeProject\ai-galgame\electron && npm run dist", 3600)
log(f"打包: {'OK' if ok else 'FAIL'} {out[-400:]}")

# 5. 更新安装版（win-unpacked 的 asar + 资源）
INSTALL = r"C:\Users\windows\AppData\Local\Programs\surrounded-by-ai-girls"
UNPACKED = r"C:\Users\windows\ZCodeProject\ai-galgame\electron\dist\win-unpacked"
if os.path.exists(UNPACKED) and os.path.exists(INSTALL):
    try:
        src_asar = os.path.join(UNPACKED, "resources", "app.asar")
        dst_asar = os.path.join(INSTALL, "resources", "app.asar")
        if os.path.exists(src_asar):
            shutil.copy2(src_asar, dst_asar)
            log(f"安装版 app.asar 已更新（{os.path.getsize(dst_asar)//1024//1024}MB）")
        # 语音等资源在 asar 内，无需额外复制
    except Exception as e:
        log(f"更新安装版失败: {e}")
else:
    log("未找到安装目录或打包产物，跳过安装版更新")

log("自动收尾完成")
