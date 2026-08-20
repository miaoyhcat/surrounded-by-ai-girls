# -*- coding: utf-8 -*-
"""TapTap 实机截图：正常游戏流程画面（带 UI），1280x720，符合 TapTap 规范"""
import os
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\windows\ZCodeProject\ai-galgame\src\web\demo"
OUT = r"C:\Users\windows\ZCodeProject\ai-galgame\store\taptap_screens"
os.makedirs(OUT, exist_ok=True)

# (场景id, 推进行数, 文件名)
SHOTS = [
    ("s1", 6,  "01_first_meet"),     # 初遇 GPT 娘
    ("s4", 3,  "02_classroom"),      # 教室
    ("s7", 2,  "03_three_on_train"), # 三人列车
    ("s13", 3, "04_whale_field"),    # 鲸鱼娘田野
    ("s16", 2, "05_gpt_un"),         # 联合国 GPT
    ("s18", 2, "06_all_home"),       # 隐藏结局全家福
]

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.add_init_script("localStorage.setItem('aigirls_name','玩家');")
    pg.goto(f"file:///{BASE}/game.html")
    pg.wait_for_timeout(1500)
    if pg.is_visible("#titleCard"):
        pg.click("#titleCard", force=True)
        pg.wait_for_timeout(800)
    # 跳转到目标场景
    for sid, advance, name in SHOTS:
        pg.evaluate(f"""
          sceneIdx = {sid and '"'+sid+'"'};
          lineIdx = 0;
          showTitle(STORY.find(s=>s.id==='{sid}'));
        """)
        pg.wait_for_timeout(400)
        if pg.is_visible("#titleCard"):
            pg.click("#titleCard", force=True)
            pg.wait_for_timeout(1000)
        # 推进到有台词的位置
        for _ in range(advance):
            pg.click("#boxInner", force=True)
            pg.wait_for_timeout(250)
        pg.wait_for_timeout(500)
        pg.screenshot(path=os.path.join(OUT, name + ".png"))
        print("OK", name)
    b.close()
print("完成:", OUT)
