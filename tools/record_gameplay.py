# -*- coding: utf-8 -*-
"""TapTap 实机录屏：Playwright 驱动游戏，1920x1080，展示对话+选择+CG"""
import os
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\windows\ZCodeProject\ai-galgame\src\web\demo"
OUT = r"C:\Users\windows\ZCodeProject\ai-galgame\store"
VID = os.path.join(OUT, "record")

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=VID,
        record_video_size={"width": 1920, "height": 1080},
    )
    pg = ctx.new_page()
    pg.add_init_script("localStorage.setItem('aigirls_name','玩家');")
    pg.goto(f"file:///{BASE}/game.html")
    pg.wait_for_timeout(2500)

    # 点击标题卡进入剧情（核心玩法 5s 内出现）
    if pg.is_visible("#titleCard"):
        pg.click("#titleCard", force=True)
    pg.wait_for_timeout(800)

    # 正常推进 8 行（开场旁白 + 角色登场，间隔 2s 展示打字）
    for i in range(8):
        pg.click("#boxInner", force=True)
        pg.wait_for_timeout(2000)

    # 跳到 choice 前 4 行（choice 在 89 行），继续自然点击（场景：深夜，她问：你会一直回我吗？）
    pg.evaluate("lineIdx = 85;")
    for i in range(4):  # 86, 87, 88, 89(choice)
        pg.click("#boxInner", force=True)
        pg.wait_for_timeout(2000)

    # choice 出现 → 选择「会」
    if pg.is_visible("#choices"):
        pg.wait_for_timeout(600)
        pg.click("#choices button[data-i="0"]", force=True)
        pg.wait_for_timeout(2500)
    # 看两句回复
    pg.click("#boxInner", force=True)
    pg.wait_for_timeout(2200)
    pg.click("#boxInner", force=True)
    pg.wait_for_timeout(2500)

    # 录屏最后再展示一下 CG（切到第二幕标题卡前）
    pg.wait_for_timeout(1000)

    pg.close()
    video = pg.video
    vpath = video.path() if video else None
    ctx.close()
    b.close()
    print("视频:", vpath)
