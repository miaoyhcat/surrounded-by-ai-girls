# -*- coding: utf-8 -*-
"""小游戏与其他功能冲突专项测试：
1. 小游戏期间按 空格/回车 不推进剧情
2. 小游戏期间按 Esc 退出小游戏继续剧情
3. 小游戏期间 Ctrl 不触发快进
4. 小游戏期间菜单按钮不可点（被覆盖）
5. 读档落在 minigame 行自动顺延
6. 历史回档不落到 minigame 行
7. 自动播放在小游戏启动时被关闭
8. 小游戏后自动播放可恢复
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

    # 打开 s1 小游戏
    pg.evaluate("""(() => {
      const si = STORY.findIndex(s => s.id === 's5b');
      const ci = STORY[si].lines.findIndex(l => l.t === 'minigame');
      sceneIdx = si; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
      document.getElementById('titleCard').style.display = 'none';
      startMinigame(STORY[si].lines[ci]);
    })()""")
    pg.wait_for_timeout(400)
    pg.click("#minigame"); pg.wait_for_timeout(1200)  # 进入 iframe

    # 1. 空格/回车不推进
    line_before = pg.evaluate("lineIdx")
    pg.keyboard.press("Space"); pg.wait_for_timeout(200)
    pg.keyboard.press("Enter"); pg.wait_for_timeout(200)
    check("F1 小游戏中空格/回车不推进剧情", pg.evaluate("lineIdx") == line_before,
          f"lineIdx={pg.evaluate('lineIdx')}")

    # 2. Ctrl 不触发快进
    pg.keyboard.down("Control"); pg.wait_for_timeout(300)
    check("F2 小游戏中 Ctrl 不触发快进", pg.evaluate("skipMode") == False)
    pg.keyboard.up("Control"); pg.wait_for_timeout(200)

    # 3. 菜单按钮被覆盖不可点
    menu_clickable = pg.evaluate("""() => {
      const btn = document.getElementById('menuBtn');
      const top = document.elementFromPoint(btn.getBoundingClientRect().x + 10, btn.getBoundingClientRect().y + 10);
      return top && top.id === 'menuBtn';
    }""")
    check("F3 小游戏中菜单被覆盖", not menu_clickable)

    # 4. 自动播放被关闭
    check("F4 小游戏启动时自动播放关闭", pg.evaluate("autoMode") == False)

    # 5. Esc 退出小游戏
    pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    check("F5 Esc 退出小游戏", pg.evaluate("document.getElementById('minigame').style.display") == "none" or
          pg.evaluate("getComputedStyle(document.getElementById('minigame')).display") == "none")
    check("F5b Esc 后继续剧情", len(pg.evaluate("document.getElementById('text').textContent")) > 0)
    check("F5c mgActive 复位", pg.evaluate("mgActive") == False)

    # 6. 读档落在 minigame 行 → 顺延
    pg.evaluate("""(() => {
      const ci = STORY.findIndex(s => s.id === 's5b');
      const mi = STORY[ci].lines.findIndex(l => l.t === 'minigame');
      const d = {scene: ci, line: mi, aff: {g:1,claude:0,whale:1}, hist: [], t: 't'};
      localStorage.setItem('aigirls_save_v1_auto', JSON.stringify(d));
    })()""")
    pg.evaluate("(location.href = location.href + '?continue=1')")
    pg.wait_for_timeout(1500)
    r = pg.evaluate("""(() => {
      const scene = STORY[sceneIdx];
      const line = scene.lines[Math.min(lineIdx, scene.lines.length-1)];
      return { lineIdx, type: line ? line.t : 'END', isMg: line ? line.t === 'minigame' : false };
    })()""")
    check("F6 读档落在小游戏行自动顺延", r["isMg"] == False and r["type"] in ("narr","g","you","whale","claude","choice","transition"), str(r))

    # 7. 历史回档不落到 minigame 行
    hist_types = pg.evaluate("history.map(h => h.t)")
    check("F7 历史无 minigame 行", "minigame" not in hist_types)

    # 8. 小游戏后自动播放可恢复
    pg.evaluate("""(() => {
      const si = STORY.findIndex(s => s.id === 's5b');
      const ci = STORY[si].lines.findIndex(l => l.t === 'minigame');
      sceneIdx = si; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
      document.getElementById('titleCard').style.display = 'none';
      startMinigame(STORY[si].lines[ci]);
    })()""")
    pg.wait_for_timeout(300)
    pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
    pg.evaluate("autoMode = true")
    check("F8 小游戏后可恢复自动播放", pg.evaluate("autoMode") == True)

    b.close()

print(f"\n===== 小游戏冲突专项: {PASS}/{PASS+FAIL} 通过 =====")
sys.exit(1 if FAIL else 0)
