# -*- coding: utf-8 -*-
"""同步 src/web/demo → electron/game（打包前执行）"""
import os, shutil, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "src", "web", "demo")
DST = os.path.join(BASE, "electron", "game")
EXCLUDE = {"voice_map.json", "_check_tmp.js"}

def sync():
    if not os.path.exists(DST):
        os.makedirs(DST)
    # 删除目标中多余文件
    for root, dirs, files in os.walk(DST):
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, DST)
            if rel not in EXCLUDE:
                os.remove(p)
        for d in dirs:
            dp = os.path.join(root, d)
            if not os.listdir(dp):
                os.rmdir(dp)
    # 复制源文件
    n = 0
    for root, dirs, files in os.walk(SRC):
        rel = os.path.relpath(root, SRC)
        target = DST if rel == "." else os.path.join(DST, rel)
        os.makedirs(target, exist_ok=True)
        for f in files:
            if f in EXCLUDE:
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(target, f))
            n += 1
    print(f"synced {n} files -> {DST}")

if __name__ == "__main__":
    sync()
