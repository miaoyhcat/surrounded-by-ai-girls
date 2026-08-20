# -*- coding: utf-8 -*-
"""wav → mp3 批量转换（游戏用 mp3 减小体积，保留音质）"""
import os, subprocess, sys

SRC = r"D:\tts_voice"
DST = r"C:\Users\windows\ZCodeProject\ai-galgame\src\web\demo\voice"

def to_mp3(src_wav, dst_mp3):
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src_wav,
         "-codec:a", "libmp3lame", "-q:a", "3", dst_mp3],
        capture_output=True, text=True)
    return r.returncode == 0

total, ok, fail = 0, 0, 0
for scene in sorted(os.listdir(SRC)):
    scene_dir = os.path.join(SRC, scene)
    if not os.path.isdir(scene_dir):
        continue
    out_scene = os.path.join(DST, scene)
    os.makedirs(out_scene, exist_ok=True)
    for n in sorted(os.listdir(scene_dir)):
        if not n.endswith(".wav"):
            continue
        total += 1
        src = os.path.join(scene_dir, n)
        dst = os.path.join(out_scene, n.replace(".wav", ".mp3"))
        if os.path.exists(dst) and os.path.getsize(dst) > 1000:
            ok += 1
            continue
        if to_mp3(src, dst):
            ok += 1
        else:
            print(f"✗ {scene}/{n}")
            fail += 1

print(f"转换完成：{ok}/{total} 成功，{fail} 失败 → {DST}")
