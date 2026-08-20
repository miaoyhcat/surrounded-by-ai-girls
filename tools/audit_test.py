# -*- coding: utf-8 -*-
"""最终全面验收：每幕 CG 实际加载 + 所有按钮/功能/流程逐一检查"""
from playwright.sync_api import sync_playwright
import os, tempfile, shutil, json

INDEX = "file:///C:/Users/windows/ZCodeProject/ai-galgame/src/web/demo/index.html"
GAME = "file:///C:/Users/windows/ZCodeProject/ai-galgame/src/web/demo/game.html"
RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), "-", name, detail)

with sync_playwright() as p:
    profile = tempfile.mkdtemp(prefix="aigirls_audit")
    ctx = p.chromium.launch_persistent_context(profile, headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:"+m.text) if m.type == "error" else None)
    pg.add_init_script("""if(!localStorage.getItem('audit_init')){
      localStorage.setItem('audit_init','1');
      localStorage.setItem('aigirls_name','验收员');
      for(const k of Object.keys(localStorage)){
        if(k.startsWith('aigirls_save_v1')||k==='aigirls_cg_unlocked') localStorage.removeItem(k);
      }
      localStorage.setItem('aigirls_settings','{}');
    }""")

    # ═══ A. 主界面按钮 ═══
    pg.goto(INDEX); pg.wait_for_timeout(800)
    check("A1 主界面标题", "完蛋" in pg.title())
    check("A2 无存档→无继续按钮", pg.evaluate("getComputedStyle(document.getElementById('btnContinue')).display") == "none")
    check("A3 开始/相册/设置按钮存在", all(pg.is_visible(f"#{b}") for b in ["btnNew","btnAlbum","btnSettings","hallNameOk","hallBgm"]))
    # 名字修改
    pg.fill("#hallName", "验收员"); pg.click("#hallNameOk"); pg.wait_for_timeout(300)
    check("A4 名字保存", pg.evaluate("localStorage.getItem('aigirls_name')") == "验收员")
    # 主界面设置
    pg.click("#btnSettings"); pg.wait_for_timeout(300)
    check("A5 主界面设置打开", pg.is_visible("#settingsPanel"))
    check("A6 设置含高中生独立研发寄语", "高中生独立研发" in pg.inner_text("#settingsPanel"))
    pg.click("#sBgm"); pg.wait_for_timeout(200)
    check("A7 主界面BGM开关", pg.evaluate("JSON.parse(localStorage.getItem('aigirls_settings')).bgm") == False)
    pg.click("#sBgm")
    pg.evaluate("document.getElementById('settingsClose').click()"); pg.wait_for_timeout(200)
    # 相册（空）
    pg.click("#btnAlbum"); pg.wait_for_timeout(300)
    n_locked = pg.evaluate("document.querySelectorAll('#albumGrid .card.locked').length")
    check("A8 相册全未解锁", n_locked == 15, f"{n_locked} 张未解锁")
    pg.evaluate("document.getElementById('albumClose').click()")

    # ═══ B. 每幕 CG 实际加载 ═══
    pg.goto(GAME + "?new=1"); pg.wait_for_timeout(1000)
    for si in range(15):
        pg.evaluate(f"""(()=>{{ sceneIdx = {si}; showTitle(STORY[{si}]); }})()""")
        pg.wait_for_timeout(250)
        # 用 Image 预加载验证 CG 文件真实可加载（非 404）
        cg_ok = pg.evaluate(f"""(()=>{{
          const url = 'assets/' + STORY[{si}].cg.split('/').pop();
          return new Promise(res=>{{
            const im = new Image();
            im.onload = ()=>res(true);
            im.onerror = ()=>res(false);
            im.src = url;
          }});
        }})()""")
        check(f"B{si+1} 幕{si+1} CG可加载", cg_ok, f"scene={si}")
    ctx.close()

    # 用 node 侧验证图片（上面 evaluate 的 STORY 引用在页面内有效）
    # 重新开 context 做按钮/流程检查
    ctx = p.chromium.launch_persistent_context(profile, headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script("""if(!localStorage.getItem('audit_init')){
      localStorage.setItem('audit_init','1');
      localStorage.setItem('aigirls_name','验收员');
      localStorage.setItem('aigirls_settings','{}');
    }""")
    pg.goto(GAME + "?new=1"); pg.wait_for_timeout(1000)
    pg.evaluate("next()"); pg.wait_for_timeout(300)  # 开始第一幕

    # ═══ C. 游戏内菜单按钮 ═══
    def menu_btn(id):
        pg.evaluate("document.querySelector('#menuBtn').click()")
        pg.wait_for_timeout(150)
        pg.evaluate(f"document.querySelector('{id}').click()")
        pg.wait_for_timeout(250)
    # C1 自动播放
    menu_btn("#mAuto")
    on = pg.evaluate("document.querySelector('#mAuto').classList.contains('on')")
    check("C1 自动播放开关", on)
    menu_btn("#mAuto")
    # C2 快进
    menu_btn("#mSkip")
    pg.wait_for_timeout(400)
    check("C2 快进开关", pg.evaluate("skipMode"))
    pg.evaluate("stopSkip()")
    # C3 快进到选项
    menu_btn("#mSkipTo")
    pg.wait_for_timeout(6000)
    st = pg.evaluate("""(()=>({inChoice: inChoice, skip: skipToChoice}))()""")
    check("C3 快进停在选项", st["inChoice"] and not st["skip"])
    pg.evaluate("document.querySelector('#choices button').click()"); pg.wait_for_timeout(300)
    # C4 设置面板
    menu_btn("#mSet")
    check("C4 设置面板", pg.is_visible("#settingsPanel"))
    check("C4b 4首曲目", pg.evaluate("document.querySelectorAll('#sBgmTrack option').length") == 4)
    check("C4c 自动速度4档", pg.evaluate("document.querySelectorAll('#sAutoSpeed option').length") == 4)
    pg.evaluate("document.querySelector('#settingsClose').click()"); pg.wait_for_timeout(200)
    # C5 历史
    menu_btn("#mHist")
    check("C5 历史打开", pg.is_visible("#history"))
    rows = pg.evaluate("document.querySelectorAll('#histList .hrow').length")
    check("C5b 历史条目>5", rows > 5, f"{rows}")
    pg.evaluate("document.querySelector('#histClose').click()"); pg.wait_for_timeout(200)
    # C6 存档 30 槽
    menu_btn("#mSave")
    n = pg.evaluate("document.querySelectorAll('#slots .slot:not([data-i=\"-1\"])').length")
    check("C6 存档30槽", n == 30, f"{n}")
    pg.evaluate("document.querySelector('#saveClose').click()"); pg.wait_for_timeout(200)
    # C7 改名
    menu_btn("#mName")
    check("C7 改名面板", pg.is_visible("#namePanel"))
    pg.fill("#nameInput", "验收员2"); pg.evaluate("document.querySelector('#nameOk').click()")
    pg.wait_for_timeout(1200)
    check("C7b 改名生效", pg.evaluate("localStorage.getItem('aigirls_name')") == "验收员2")
    # C8 返回主界面
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(150)
    with pg.expect_navigation(timeout=4000) as _:
        pg.evaluate("document.querySelector('#mHome').click()")
    check("C8 返回主界面", "index.html" in pg.url)
    # C9 主界面现在有继续按钮（自动存档在）
    check("C9 有存档→继续按钮", pg.evaluate("getComputedStyle(document.getElementById('btnContinue')).display") == "block")
    check("C10 页面错误", len(errs) == 0, "; ".join(errs[:3]))

    ctx.close()
    shutil.rmtree(profile, ignore_errors=True)

fails = [r for r in RESULTS if not r[1]]
print(f"\n===== 结果：{len(RESULTS)-len(fails)}/{len(RESULTS)} 通过 =====")
if fails:
    for f in fails: print("FAIL:", f[0], f[2])
    import sys; sys.exit(1)
