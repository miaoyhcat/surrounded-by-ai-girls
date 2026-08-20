# -*- coding: utf-8 -*-
"""剧情 CG 裁剪为 16:9（中心裁剪保留主体，统一 1366x768）
排除：main_hall_bg（首页大厅）、whale_icon（图标）、已是 16:9 的
"""
from PIL import Image
import os, shutil

ASSETS = r"C:\Users\windows\ZCodeProject\ai-galgame\src\web\demo\assets"
BACKUP = r"D:\tts_scripts\cg_backup"
os.makedirs(BACKUP, exist_ok=True)

TARGET_W, TARGET_H = 1366, 768
EXCLUDE = {"main_hall_bg.png", "whale_icon_v1.png", "claude_sheet_v1.png"}

changed, skipped = [], []
for n in sorted(os.listdir(ASSETS)):
    if not n.endswith((".png", ".jpg", ".webp")):
        continue
    if n in EXCLUDE:
        skipped.append(f"{n}（排除）")
        continue
    p = os.path.join(ASSETS, n)
    try:
        im = Image.open(p)
    except Exception:
        continue
    w, h = im.size
    if abs(w / h - 16 / 9) < 0.02:
        skipped.append(f"{n}（已是16:9 {w}x{h}）")
        continue
    # 备份
    shutil.copy2(p, os.path.join(BACKUP, n))
    # 中心裁剪到 16:9（保留主体，裁掉上下边缘）
    target_h = int(w * TARGET_H / TARGET_W)  # 按宽度等比算目标高度
    if target_h > h:
        # 图片太窄：裁宽度
        target_w = int(h * TARGET_W / TARGET_H)
        left = (w - target_w) // 2
        im2 = im.crop((left, 0, left + target_w, h))
    else:
        top = (h - target_h) // 2
        im2 = im.crop((0, top, w, top + target_h))
    # 缩放到 1366x768
    im2 = im2.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    im2.save(p)
    changed.append(f"{n}: {w}x{h} → 1366x768")

print("=== 已裁剪（保留主体，16:9）===")
for c in changed:
    print(" ", c)
print(f"\n共裁剪 {len(changed)} 张，跳过 {len(skipped)} 张（未改动）")
print("备份在:", BACKUP)
