# -*- coding: utf-8 -*-
"""模拟玩家全功能测试 v2（persistent context 模拟真实大退重进）
重点：多次大退游戏再进入，检查进度与状态是否正常
"""
from playwright.sync_api import sync_playwright
import os, shutil, tempfile

INDEX = "file:///C:/Users/windows/ZCodeProject/ai-galgame/src/web/demo/index.html"
GAME = "file:///C:/Users/windows/ZCodeProject/ai-galgame/src/web/demo/game.html"
RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), "-", name, detail)

def reset_ctx(p, profile):
    ctx = p.chromium.launch_persistent_context(profile, headless=True)
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.add_init_script("""if(!localStorage.getItem('sim_init_done')){
      localStorage.setItem('sim_init_done','1');
      localStorage.setItem('aigirls_name','模拟玩家');
      localStorage.removeItem('aigirls_save_v1_auto');
      localStorage.removeItem('aigirls_save_v1_0');
      localStorage.removeItem('aigirls_save_v1_1');
      localStorage.removeItem('aigirls_save_v1_2');
      localStorage.removeItem('aigirls_cg_unlocked');
      localStorage.setItem('aigirls_settings','{}');
    }""")
    return ctx, pg

def play_forward(pg, target_scene, max_steps=600):
    """模拟玩家点推进直到到达目标幕或步数用尽"""
    for i in range(max_steps):
        s = pg.evaluate("sceneIdx")
        if s >= target_scene:
            return True
        pg.evaluate("next()")
        if pg.evaluate("document.getElementById('choices').style.display === 'flex'"):
            pg.evaluate("document.querySelector('#choices button').click()")
        if pg.evaluate("document.getElementById('trans').style.display === 'flex'"):
            pg.evaluate("document.querySelector('#trans').click()")
    return pg.evaluate("sceneIdx") >= target_scene

with sync_playwright() as p:
    profile = tempfile.mkdtemp(prefix="aigirls_profile")

    # ========== 第一轮：全新开始 ==========
    ctx, pg = reset_ctx(p, profile)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(INDEX); pg.wait_for_timeout(700)
    check("主界面:无继续按钮(无存档)", pg.evaluate("getComputedStyle(document.getElementById('btnContinue')).display") == "none")
    pg.evaluate("document.getElementById('btnNew').click()")
    pg.wait_for_timeout(1000)
    check("开始游戏→从头(URL参数已清理)", "game.html" in pg.url)
    check("从头开始=第一幕", "第一夜" in pg.inner_text("#tcTitle"))
    pg.click("#titleCard"); pg.wait_for_timeout(300)
    ok = play_forward(pg, 1)
    check("推进到幕2", ok, f"scene={pg.evaluate('sceneIdx')}")
    check("自动存档已写", pg.evaluate("!!localStorage.getItem('aigirls_save_v1_auto')"))
    n_unlock = pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('aigirls_cg_unlocked')||'{}')).length")
    check("CG解锁记录≥2", n_unlock >= 2, f"{n_unlock}张")
    ctx.close(); print("--- 大退 #1 ---")

    # ========== 第二轮：继续游戏 ==========
    ctx, pg = reset_ctx(p, profile)
    pg.goto(INDEX); pg.wait_for_timeout(700)
    check("主界面:继续按钮出现", pg.evaluate("getComputedStyle(document.getElementById('btnContinue')).display") == "block")
    pg.evaluate("document.getElementById('btnContinue').click()")
    pg.wait_for_timeout(1500)
    check("继续→加载游戏页", "game.html" in pg.url)
    s = pg.evaluate("sceneIdx")
    check("继续=恢复幕2", s == 1, f"scene={s}")
    check("名字保持", pg.evaluate("localStorage.getItem('aigirls_name')") == "模拟玩家")
    # 再玩到幕3
    ok = play_forward(pg, 2)
    check("继续后推进到幕3", ok, f"scene={pg.evaluate('sceneIdx')}")
    ctx.close(); print("--- 大退 #2 ---")

    # ========== 第三轮：再继续（多次大退） ==========
    ctx, pg = reset_ctx(p, profile)
    pg.goto(INDEX); pg.wait_for_timeout(700)
    pg.evaluate("document.getElementById('btnContinue').click()")
    pg.wait_for_timeout(1500)
    check("二次大退后继续=幕3", pg.evaluate("sceneIdx") == 2, f"scene={pg.evaluate('sceneIdx')}")
    ctx.close(); print("--- 大退 #3 ---")

    # ========== 第四轮：三次大退后继续 + 相册 ==========
    ctx, pg = reset_ctx(p, profile)
    pg.goto(INDEX); pg.wait_for_timeout(700)
    pg.evaluate("document.getElementById('btnContinue').click()")
    pg.wait_for_timeout(1500)
    check("三次大退后继续正常", pg.evaluate("sceneIdx") == 2)
    # 相册
    pg.evaluate("location.href='index.html'"); pg.wait_for_timeout(800)
    pg.evaluate("document.getElementById('btnAlbum').click()")
    pg.wait_for_timeout(400)
    n_un = pg.evaluate("document.querySelectorAll('#albumGrid .card:not(.locked)').length")
    n_lk = pg.evaluate("document.querySelectorAll('#albumGrid .card.locked').length")
    check("相册:已解锁≥3", n_un >= 3, f"{n_un}张解锁")
    check("相册:有未解锁", n_lk >= 1, f"{n_lk}张未解锁")
    check("相册:卡片含图", pg.evaluate("!!document.querySelector('#albumGrid .card img')"))
    pg.evaluate("document.getElementById('albumClose').click()")
    check("相册关闭", pg.evaluate("getComputedStyle(document.getElementById('albumPanel')).display") == "none")
    ctx.close()

    # ========== 第五轮：游戏内设置/回档/主界面BGM ==========
    ctx, pg = reset_ctx(p, profile)
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(GAME + "?new=1"); pg.wait_for_timeout(800)
    pg.click("#titleCard"); pg.wait_for_timeout(300)
    for i in range(12): pg.evaluate("next()")
    pg.wait_for_timeout(300)
    # 游戏内 BGM
    st = pg.evaluate("""(()=>({src: bgmAudio.src.slice(-22), paused: bgmAudio.paused}))()""")
    check("游戏内BGM播放", st["paused"] == False, st["src"])
    # 设置面板：自动播放速度 + 其他寄语
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelector('#mSet').click()"); pg.wait_for_timeout(300)
    check("设置含自动速度", pg.evaluate("!!document.querySelector('#sAutoSpeed')"))
    check("设置含其他寄语", "谨以此游戏" in pg.inner_text("#settingsPanel"))
    pg.evaluate("document.querySelector('#sAutoSpeed').value='3'; document.querySelector('#sAutoSpeed').dispatchEvent(new Event('change'))")
    check("自动速度保存=3", pg.evaluate("JSON.parse(localStorage.getItem('aigirls_settings')).autoSpeed") == 3)
    pg.evaluate("document.querySelector('#mAuto').click()"); pg.wait_for_timeout(300)
    check("快档延迟2200", pg.evaluate("autoDelay()") == 2200)
    pg.evaluate("document.querySelector('#mAuto').click()")
    pg.evaluate("document.querySelector('#settingsClose').click()")
    # 历史回档
    pg.evaluate("document.querySelector('#mHist').click()"); pg.wait_for_timeout(300)
    rows = pg.evaluate("document.querySelectorAll('#histList .hrow').length")
    check("历史有条目", rows > 3, f"{rows}条")
    pg.evaluate("document.querySelectorAll('#histList .hrow')[1].click()")
    pg.wait_for_timeout(400)
    check("回档后关闭", pg.evaluate("getComputedStyle(document.getElementById('history')).display") == "none")
    # 主界面 BGM 开关
    pg.evaluate("location.href='index.html'"); pg.wait_for_timeout(800)
    pg.evaluate("document.getElementById('hallBgm').click()")
    check("主界面BGM关闭", pg.evaluate("JSON.parse(localStorage.getItem('aigirls_settings')).bgm") == False)
    pg.evaluate("document.getElementById('hallBgm').click()")
    check("主界面BGM再开", pg.evaluate("JSON.parse(localStorage.getItem('aigirls_settings')).bgm") == True)
    check("页面错误", len(errs) == 0, "; ".join(errs[:3]))
    ctx.close()

    # 清理
    shutil.rmtree(profile, ignore_errors=True)

fails = [r for r in RESULTS if not r[1]]
print(f"\n===== 结果：{len(RESULTS)-len(fails)}/{len(RESULTS)} 通过 =====")
if fails:
    for f in fails: print("FAIL:", f[0], f[2])
    import sys; sys.exit(1)
