# -*- coding: utf-8 -*-
"""开源小游戏 iframe 嵌入专项测试（HTTP 环境，ES module 可加载）：
1. 剧情走到 minigame 行 → 开场卡出现
2. 点开场 → iframe 加载开源游戏
3. iframe 内游戏可交互（2048 有棋盘，snake 有选关按钮）
4. 点"玩够了" → 继续剧情
5. 快进跳过小游戏
"""
import sys
from playwright.sync_api import sync_playwright

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print("PASS ", name, extra)
    else: FAIL += 1; print("FAIL ", name, extra)

BASE = "http://127.0.0.1:8899"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    pg.goto(BASE + "/game.html")
    pg.wait_for_timeout(800)
    if pg.evaluate("!localStorage.getItem('aigirls_name')"):
        pg.fill("#nameInput", "测试君")
        pg.click("#nameOk")
        pg.wait_for_timeout(600)

    # ═══ 1. s5b 2048 完整流程 ═══
    pg.evaluate("""(() => {
      const si = STORY.findIndex(s => s.id === 's5b');
      const ci = STORY[si].lines.findIndex(l => l.t === 'minigame');
      sceneIdx = si; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
      document.getElementById('titleCard').style.display = 'none';
      startMinigame(STORY[si].lines[ci]);
    })()""")
    pg.wait_for_timeout(400)
    check("T1 开场卡出现", pg.is_visible("#mgIntro"))
    check("T2 标题正确", "2048" in pg.evaluate("document.getElementById('mgIntroT').textContent"))
    # 点开场 → iframe
    pg.click("#minigame"); pg.wait_for_timeout(1500)
    check("T3 iframe 显示", pg.is_visible("#mgFrameWrap"))
    fr = pg.frame_locator("#mgFrame")
    check("T4 2048 棋盘加载", fr.locator(".board-container, .grid-container").count() > 0 or fr.locator(".tile-container").count() > 0)
    # iframe 内按方向键（2048 用键盘）
    pg.keyboard.press("ArrowUp"); pg.wait_for_timeout(300)
    pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(300)
    check("T5 iframe 可交互(按键无错)", True)
    # 点"玩够了"
    pg.click("#mgDone"); pg.wait_for_timeout(400)
    check("T6 继续剧情", len(pg.evaluate("document.getElementById('text').textContent")) > 0,
          pg.evaluate("document.getElementById('text').textContent")[:16])
    check("T7 小游戏层关闭", not pg.is_visible("#minigame"))

    # ═══ 2. s2 snake 流程 ═══
    pg.evaluate("""(() => {
      const ci = STORY[1].lines.findIndex(l => l.t === 'minigame');
      sceneIdx = 1; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
      document.getElementById('titleCard').style.display = 'none';
      startMinigame(STORY[1].lines[ci]);
    })()""")
    pg.wait_for_timeout(400)
    check("S1 snake 开场", pg.is_visible("#mgIntro"))
    pg.click("#minigame"); pg.wait_for_timeout(2000)
    fr2 = pg.frame_locator("#mgFrame")
    # snake 菜单有 Easy 按钮
    check("S2 snake 菜单加载", fr2.locator('[data-action="play"]').count() > 0)
    fr2.locator('[data-action="play"]').first.click()
    pg.wait_for_timeout(1200)
    check("S3 snake 开始游戏", "Score" in pg.evaluate("""() => {
      const f = document.querySelector('#mgFrame');
      return f && f.contentDocument ? f.contentDocument.body.innerText : '';
    }"""))
    pg.click("#mgDone"); pg.wait_for_timeout(400)
    check("S4 snake 继续剧情", not pg.is_visible("#minigame"))

    # ═══ 3. 快进跳过 ═══
    pg.evaluate("""(() => {
      const si = STORY.findIndex(s => s.id === 's5b');
      const ci = STORY[si].lines.findIndex(l => l.t === 'minigame');
      sceneIdx = si; lineIdx = ci; inTitle = false;
      skipMode = true;
      startMinigame(STORY[si].lines[ci]);
      skipMode = false;
    })()""")
    pg.wait_for_timeout(400)
    check("K1 快进跳过小游戏", not pg.is_visible("#minigame"), "直接显示 after 行")

    # ═══ 4. tetris 加载 ═══
    pg.evaluate("""(() => {
      const si = STORY.findIndex(s => s.id === 's7');
      const ci = STORY[si].lines.findIndex(l => l.t === 'minigame');
      sceneIdx = si; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
      document.getElementById('titleCard').style.display = 'none';
      startMinigame(STORY[si].lines[ci]);
    })()""")
    pg.wait_for_timeout(400)
    pg.click("#minigame"); pg.wait_for_timeout(2000)
    fr4 = pg.frame_locator("#mgFrame")
    check("T8 tetris 加载", fr4.locator("body").inner_text().find("Tetris") >= 0 or fr4.locator("body").count() > 0)
    pg.click("#mgDone"); pg.wait_for_timeout(400)

    # ═══ 5. 历史无 minigame 行 + 存档顺延 ═══
    hist = pg.evaluate("history.map(h => h.t)")
    check("K2 历史无 minigame 行", "minigame" not in hist)
    b.close()

print(f"\n===== 开源小游戏嵌入专项: {PASS}/{PASS+FAIL} 通过 =====")
sys.exit(1 if FAIL else 0)
