# -*- coding: utf-8 -*-
"""存档/读档 专项深度测试：多角度验证
覆盖：3槽存取/覆盖/空槽、精确位置恢复、choice行/transition行存档、
多槽来回切换、跨场景、读档后回档/自动播放/BGM、自动存档位置正确性
"""
from playwright.sync_api import sync_playwright
import os, tempfile, shutil

GAME = "file:///C:/Users/windows/ZCodeProject/ai-galgame/src/web/demo/game.html"
RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), "-", name, detail)

def fresh(pg, profile_first=False):
    pg.add_init_script("""if(!localStorage.getItem('save_test_init')){
      localStorage.setItem('save_test_init','1');
      localStorage.setItem('aigirls_name','存档测试');
      for(const k of Object.keys(localStorage)){
        if(k.startsWith('aigirls_save_v1') || k==='aigirls_cg_unlocked') localStorage.removeItem(k);
      }
      localStorage.setItem('aigirls_settings','{}');
    }""")

with sync_playwright() as p:
    profile = tempfile.mkdtemp(prefix="aigirls_save")
    ctx = p.chromium.launch_persistent_context(profile, headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    fresh(pg)
    pg.goto(GAME + "?new=1"); pg.wait_for_timeout(800)
    pg.click("#titleCard"); pg.wait_for_timeout(300)

    # ---- 1. 推进到幕1 第30行左右，存档到槽1 ----
    for i in range(60):
        if pg.evaluate("STORY[sceneIdx] && STORY[sceneIdx].lines[lineIdx] && STORY[sceneIdx].lines[lineIdx].t === 'minigame'"):
            pg.evaluate("lineIdx++; autoSave()")
        pg.evaluate("next()")
    pg.wait_for_timeout(300)
    s1_scene = pg.evaluate("sceneIdx"); s1_line = pg.evaluate("lineIdx")
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mSave').click()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#slots .slot')[0].click()")  # 槽1
    pg.wait_for_timeout(300)
    saved1 = pg.evaluate("JSON.parse(localStorage.getItem('aigirls_save_v1_0'))")
    check("存档1:位置记录", saved1 and saved1["scene"] == s1_scene and abs(saved1["line"] - s1_line) <= 2,
          f"存时 scene={s1_scene} line={s1_line} → 档 scene={saved1["scene"]} line={saved1["line"]}")
    check("存档1:好感记录", "aff" in saved1 and saved1["aff"]["g"] >= 1)
    pg.evaluate("document.querySelector('#saveClose').click()")

    # ---- 2. 继续玩到幕3，存档到槽2 ----
    for i in range(400):
        if pg.evaluate("STORY[sceneIdx] && STORY[sceneIdx].lines[lineIdx] && STORY[sceneIdx].lines[lineIdx].t === 'minigame'"):
            pg.evaluate("lineIdx++; autoSave()")
        pg.evaluate("next()")
        if pg.evaluate("document.getElementById('choices').style.display === 'flex'"):
            pg.evaluate("document.querySelector('#choices button').click()")
        if pg.evaluate("document.getElementById('trans').style.display === 'flex'"):
            pg.evaluate("document.querySelector('#trans').click()")
        if pg.evaluate("sceneIdx") >= 2: break
    pg.wait_for_timeout(300)
    s2_scene = pg.evaluate("sceneIdx"); s2_line = pg.evaluate("lineIdx")
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mSave').click()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#slots .slot')[1].click()")  # 槽2
    pg.wait_for_timeout(300)
    saved2 = pg.evaluate("JSON.parse(localStorage.getItem('aigirls_save_v1_1'))")
    check("存档2:幕3位置", saved2["scene"] == 2, f"scene={saved2["scene"]}")
    pg.evaluate("document.querySelector('#saveClose').click()")

    # ---- 3. 读档1 → 应回幕1/2附近 ----
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mLoad').click()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#slots .slot')[0].click()")  # 读槽1
    pg.wait_for_timeout(500)
    s3_scene = pg.evaluate("sceneIdx"); s3_line = pg.evaluate("lineIdx")
    check("读档1:回到保存位置", s3_scene == saved1["scene"] and abs(s3_line - saved1["line"]) <= 1,
          f"scene={s3_scene} line={s3_line} (档: {saved1["scene"]}/{saved1["line"]})")
    t = pg.evaluate("document.querySelector('#text').textContent.slice(0,12)")
    check("读档1:文本显示", len(t) > 0, f"[{t}]")
    check("读档1:好感恢复", pg.evaluate("AFF.g") == saved1["aff"]["g"], f"g={pg.evaluate('AFF.g')}")

    # ---- 4. 读档2 → 应回幕3 ----
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mLoad').click()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#slots .slot')[1].click()")
    pg.wait_for_timeout(500)
    check("读档2:回到幕3", pg.evaluate("sceneIdx") == 2, f"scene={pg.evaluate('sceneIdx')}")

    # ---- 5. 读档后继续推进 + 自动播放 ----
    for i in range(30):
        pg.evaluate("next()")
        if pg.evaluate("document.getElementById('choices').style.display === 'flex'"):
            pg.evaluate("document.querySelector('#choices button').click()")
    pg.wait_for_timeout(300)
    check("读档后继续推进正常", pg.evaluate("lineIdx") > saved2["line"], f"line={pg.evaluate('lineIdx')}")

    # ---- 6. choice 行存档：跳到 choice 行前一行（跳过 minigame），存档，读档后选项可点 ----
    pg.evaluate("""(()=>{ sceneIdx = 0;
      const s = STORY[0];
      const ci = s.lines.findIndex(l => l.t === 'choice');
      let pi = ci - 1;
      while(pi > 0 && s.lines[pi].t === 'minigame') pi--;
      lineIdx = pi; document.getElementById('cg').style.backgroundImage='url('+s.cg+')'; showLine(s.lines[pi]); })()""")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mSave').click()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#slots .slot')[2].click()")  # 槽3
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#saveClose').click()")
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mLoad').click()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#slots .slot')[2].click()")
    pg.wait_for_timeout(400)
    # 前进几步应到 choice（经过 minigame 行则跳过）
    for i in range(8):
        if pg.evaluate("STORY[sceneIdx] && STORY[sceneIdx].lines[lineIdx] && STORY[sceneIdx].lines[lineIdx].t === 'minigame'"):
            pg.evaluate("lineIdx++; autoSave()")
        pg.evaluate("next()")
        if pg.evaluate("document.getElementById('choices').style.display === 'flex'"):
            break
    check("choice前存档→读档→选项出现", pg.evaluate("document.getElementById('choices').style.display") == "flex")
    pg.evaluate("document.querySelector('#choices button').click()")
    pg.wait_for_timeout(300)
    check("读档后选项可选", pg.evaluate("document.getElementById('choices').style.display") == "none")

    # ---- 7. 空槽读档提示 ----
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mLoad').click()")
    pg.wait_for_timeout(300)
    # 没有第4个手动槽（3个），检查空槽 alert：用 JS 拦截 alert
    pg.evaluate("window.__alerts=[]; window.alert=(m)=>{window.__alerts.push(m)}")
    # 清掉槽3再读
    pg.evaluate("localStorage.removeItem('aigirls_save_v1_2')")
    pg.evaluate("document.querySelector('#mLoad').click()")  # 重新渲染
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('#slots .slot')[2].click()")
    pg.wait_for_timeout(300)
    check("空槽读档有提示", pg.evaluate("window.__alerts.length") >= 1)
    pg.evaluate("document.querySelector('#saveClose').click()")

    # ---- 8. 自动存档正确性：choice reply 后自动存档位置 = choice+1 ----
    pg.evaluate("""(()=>{ sceneIdx = 0; const s=STORY[0]; let ci = s.lines.findIndex(l=>l.t==='choice'); lineIdx = ci; showChoice(s.lines[ci]); })()""")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#choices button').click()")
    pg.wait_for_timeout(400)
    auto = pg.evaluate("""(() => {
      const a = JSON.parse(localStorage.getItem('aigirls_save_v1_auto'));
      const ci = STORY[0].lines.findIndex(l=>l.t==='choice');
      return {scene: a.scene, line: a.line, ci, ok: a.scene === 0 && a.line === ci};
    })()""")
    check("自动存档=choice行", auto["ok"], f"scene={auto["scene"]} line={auto["line"]} (choice={auto["ci"]})")

    # ---- 9. 读档后 BGM 启动 ----
    pg.evaluate("""(()=>{ sceneIdx = 2; lineIdx = 10; const d = {scene:2, line:10, aff:{g:1,claude:0,whale:1}, hist:[]}; localStorage.setItem('aigirls_save_v1_auto', JSON.stringify(d)); })()""")
    pg.goto(GAME + "?continue=1"); pg.wait_for_timeout(1000)
    bgm_paused = pg.evaluate("bgmAudio.paused")
    check("继续游戏后BGM启动", bgm_paused == False, f"paused={bgm_paused}")
    check("读档后场景正确", pg.evaluate("sceneIdx") == 2)

    check("无页面错误", len(errs) == 0, "; ".join(errs[:3]))
    ctx.close()
    shutil.rmtree(profile, ignore_errors=True)

fails = [r for r in RESULTS if not r[1]]
print(f"\n===== 结果：{len(RESULTS)-len(fails)}/{len(RESULTS)} 通过 =====")
if fails:
    for f in fails: print("FAIL:", f[0], f[2])
    import sys; sys.exit(1)
