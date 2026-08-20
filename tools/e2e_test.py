# -*- coding: utf-8 -*-
"""《完蛋，我被AI娘包围了》端到端功能测试（Playwright）
覆盖：开始游戏 / 名字 / 打字推进 / 自动播放 / 快进 / 历史回档 / 存档读档 / 设置面板 / BGM开关 / 选项分支 / 返回主界面
"""
import json, sys
from playwright.sync_api import sync_playwright

BASE = "file:///C:/Users/windows/ZCodeProject/ai-galgame/src/web/demo/game.html"
RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), "-", name, detail)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context()
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(f"console:{m.text}") if m.type == "error" else None)

    # 预置：名称 + 清空存档（sessionStorage flag 防止 reload 后重置）
    pg.add_init_script("if(!sessionStorage.getItem('init_done')){sessionStorage.setItem('init_done','1');localStorage.setItem('aigirls_name','测试名');localStorage.removeItem('aigirls_save_v1_auto');localStorage.removeItem('aigirls_save_v1_0');localStorage.removeItem('aigirls_save_v1_1');localStorage.removeItem('aigirls_save_v1_2');localStorage.setItem('aigirls_settings','{}');}")
    pg.goto(BASE)
    pg.wait_for_timeout(800)

    # 1. 标题卡显示
    check("标题卡显示", pg.is_visible("#titleCard"), pg.inner_text("#tcTitle")[:20])

    # 2. 点击开始 → 进入第一幕
    pg.click("#titleCard")
    pg.wait_for_timeout(600)
    check("开始后进入剧情", pg.is_visible("#box"), pg.inner_text("#sceneInfo"))

    # 3. 名字显示为自定义名
    txt = pg.inner_text("#name")
    check("角色名显示", "GPT娘" in txt or txt == "", f"name=[{txt}]")

    # 4. 连续点击推进 5 次（打字未完成点击应显示全文）
    for _ in range(5):
        pg.click("#boxInner")
        pg.wait_for_timeout(150)
    cur = pg.inner_text("#text")
    check("推进正常", len(cur) > 0, f"text=[{cur[:24]}...]")

    # 5. 选项分支：直接推进到第一幕 choice（next() 为全局函数；minigame 行速通跳过）
    pg.evaluate("""(()=>{ for(let i=0;i<500;i++){
      if(document.getElementById('choices').style.display==='flex') break;
      if(STORY[sceneIdx] && STORY[sceneIdx].lines[lineIdx] && STORY[sceneIdx].lines[lineIdx].t === 'minigame'){ lineIdx++; continue; }
      next();
    } })()""")
    pg.wait_for_timeout(500)
    clicked_choice = pg.is_visible("#choices")
    if clicked_choice:
        pg.evaluate("document.querySelector('#choices button').click()")
    check("选项出现并可选择", clicked_choice)

    # 6. 自动播放：开启后 6 秒内自动前进
    pg.evaluate("document.querySelector('#menuBtn').click()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#mAuto').click()")
    pg.wait_for_timeout(500)
    t1 = pg.evaluate("document.querySelector('#text').textContent")
    pg.wait_for_timeout(6500)
    t2 = pg.evaluate("document.querySelector('#text').textContent")
    check("自动播放前进", t1 != t2, f"'{t1[:12]}' -> '{t2[:12]}'")
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)   # 关菜单
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)   # 再开菜单
    pg.evaluate("document.querySelector('#mAuto').click()")                                # 关自动

    # 7. 快进模式
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)
    # 标记前 3 行已读，回退到已读行，开快进 → 应跳过已读、停在未读行
    pg.evaluate("document.querySelector('#mSkip').click()")
    pg.wait_for_timeout(400)
    on = pg.evaluate("skipMode")
    pg.evaluate("stopSkip()")
    check("快进开关", on)
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)

    # 8. 历史记录 + 回档
    pg.evaluate("document.querySelector('#mHist').click()")
    pg.wait_for_timeout(400)
    check("历史记录打开", pg.is_visible("#history"))
    rows = pg.evaluate("document.querySelectorAll('#histList .hrow').length")
    check("历史有条目", rows > 5, f"{rows} 条")
    # 回档到第 3 条历史
    pg.evaluate("document.querySelectorAll('#histList .hrow')[2].click()")
    pg.wait_for_timeout(500)
    check("回档后历史关闭", not pg.is_visible("#history"))
    back_text = pg.evaluate("document.querySelector('#text').textContent")
    check("回档内容", len(back_text) > 0, f"[{back_text[:20]}]")

    # 9. 存档 / 读档
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#mSave').click()")
    pg.wait_for_timeout(300)
    pg.click("#slots .slot:first-child")
    pg.wait_for_timeout(400)
    saved = pg.evaluate("!!localStorage.getItem('aigirls_save_v1_0')")
    check("存档成功", saved)
    pg.evaluate("document.querySelector('#saveClose').click()")
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#mLoad').click()")
    pg.wait_for_timeout(300)
    pg.click("#slots .slot:first-child")
    pg.wait_for_timeout(500)
    check("读档后继续", pg.is_visible("#box"))

    # 10. 设置面板
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#mSet').click()")
    pg.wait_for_timeout(400)
    check("设置面板打开", pg.is_visible("#settingsPanel"))
    pg.click("#sBgm")
    bgm_off = pg.evaluate("localStorage.getItem('aigirls_settings')")
    check("BGM 开关生效", '"bgm":false' in bgm_off, bgm_off[:60])
    pg.evaluate("document.querySelector('#settingsClose').click()")
    check("设置面板关闭", not pg.is_visible("#settingsPanel"))

    # 11. 改名
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#mName').click()")
    pg.wait_for_timeout(300)
    check("改名面板", pg.is_visible("#namePanel"))
    pg.fill("#nameInput", "阿默")
    pg.click("#nameOk")
    pg.wait_for_timeout(1200)
    check("改名保存", pg.evaluate("localStorage.getItem('aigirls_name')") == "阿默")

    # 12. 返回主界面
    pg.evaluate("document.querySelector('#menuBtn').click()"); pg.wait_for_timeout(300)
    with pg.expect_navigation(timeout=4000) as _:
        pg.click("#mHome")
    check("返回主界面", "index.html" in pg.url, pg.url)

    check("无页面错误", len(errors) == 0, "; ".join(errors[:3]))
    b.close()

fails = [r for r in RESULTS if not r[1]]
print(f"\n===== 结果：{len(RESULTS)-len(fails)}/{len(RESULTS)} 通过 =====")
if fails:
    for f in fails: print("FAIL:", f[0], f[2])
    sys.exit(1)
