# -*- coding: utf-8 -*-
"""外层循环：每 20 句重启合成进程（防 GPU 速度退化），直到全部完成"""
import os, subprocess, sys, time

BASE = r"C:\Users\windows\ZCodeProject\ai-galgame\tools"
PY = sys.executable

for round_no in range(1, 60):  # 最多 60 轮
    env = dict(os.environ, TTS_MAX_JOBS="6", PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    log = rf"D:\tts_scripts\batch_round{round_no}.log"
    r = subprocess.run([PY, os.path.join(BASE, "tts_batch_voice.py")],
                       env=env, cwd=BASE, stdout=open(log, "w", encoding="utf-8"))
    # 检查是否全部完成
    total = 0
    for root, _, files in os.walk(r"D:\tts_voice"):
        total += sum(1 for f in files if f.endswith(".wav") and os.path.getsize(os.path.join(root, f)) > 1000)
    print(f"第 {round_no} 轮完成（exit={r.returncode}），当前 {total} 个文件", flush=True)
    if total >= 662:
        print("全部完成！", flush=True)
        break
    time.sleep(3)

print("外层循环结束")
