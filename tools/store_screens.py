# -*- coding: utf-8 -*-
"""商店截图 v2：直接设置 #cg 背景图截取纯净 CG（不依赖剧情状态机）"""
import os
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\windows\ZCodeProject\ai-galgame\src\web\demo"
OUT = r"C:\Users\windows\ZCodeProject\ai-galgame\store\screenshots"
os.makedirs(OUT, exist_ok=True)

# (CG 文件名, 截图名)
SHOTS = [
    ("ch0_first_meet.png", "01_first_meet"),
    ("ch1_campus_run.png", "02_campus_run"),
    ("ch1_study_night.png", "03_study_night"),
    ("ch2_classroom.png", "04_classroom"),
    ("ch3_train_dusk.png", "05_train_dusk"),
    ("ch3_whale_arrival.png", "06_whale_arrival"),
    ("ch4_train_three.png", "07_three_on_train"),
    ("ch5_library_sleep.png", "08_library_sleep"),
    ("ch6_claude_arrival.png", "09_claude_arrival"),
    ("ch7_bed_time.png", "10_bed_time"),
    ("ch8_whale_field.png", "11_whale_field"),
    ("ch9_claude_whitehouse.png", "12_whitehouse"),
    ("ch10_gpt_un.png", "13_gpt_un"),
    ("ch11_final.png", "14_final_party"),
    ("ch12_all_home.png", "15_all_home"),
    ("ch13_market_walk.png", "16_market_walk"),
    ("main_hall_bg.png", "17_main_hall"),
]

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    pg.add_init_script("localStorage.setItem('aigirls_name','玩家');")
    pg.goto(f"file:///{BASE}/game.html")
    pg.wait_for_timeout(1500)
    # 隐藏所有 UI
    pg.evaluate("""
      const h = document.createElement('style');
      h.textContent = '#box,#hint,#menuBtn,#top,#choices,#trans,#titleCard,#namePanel,#clickLayer{display:none!important}';
      document.head.appendChild(h);
    """)
    pg.wait_for_timeout(300)
    for cg, name in SHOTS:
        # 直接设置背景（background-size 改成 cover 铺满）
        pg.evaluate(f"""
          const el = document.getElementById('cg');
          el.style.backgroundImage = 'url(assets/{cg})';
          el.style.backgroundSize = 'cover';
          el.style.backgroundPosition = 'center';
        """)
        pg.wait_for_timeout(600)
        pg.screenshot(path=os.path.join(OUT, name + ".png"))
        print("OK", name)

    # 主界面（带 UI 的完整界面截图）
    pg.goto(f"file:///{BASE}/index.html")
    pg.wait_for_timeout(1200)
    pg.screenshot(path=os.path.join(OUT, "00_main_menu.png"))
    print("OK main menu")

    b.close()
print("\n全部截图完成:", OUT)
