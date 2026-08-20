# -*- coding: utf-8 -*-
"""模拟正常玩家：在每个小游戏之前的剧情点手动存档（槽位 1/2/3），并验证读档。
流程：
1. 清空旧存档 → 开局输入名字（模拟新玩家）
2. 推进剧情（next() 等价点击；choice 自动选第一项；minigame 行顺延跳过）
3. 到达小游戏前一行 → 真实点击「存档」按钮 → 点击槽位保存
4. 验证 3 个槽位 JSON 内容（scene/line 应落在小游戏前一行）
5. 读档验证：真实点击「读档」→ 点槽位 → 显示存档点文本 → 再点击进入小游戏开场卡
"""
import json
import sys
from playwright.sync_api import sync_playwright

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print("PASS ", name, extra)
    else: FAIL += 1; print("FAIL ", name, extra)

BASE = "http://127.0.0.1:8899"
SLOT_MAP = {1: 0, 2: 1, 3: 2}  # 小游戏顺序 -> 槽位 data-i

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 800})

    # 新玩家初始化：清空全部存档 + 设置名字
    pg.add_init_script("""(() => {
      if (sessionStorage.getItem('init_done')) return;
      sessionStorage.setItem('init_done', '1');
      localStorage.removeItem('aigirls_name');
      localStorage.removeItem('aigirls_save_v1_auto');
      for (let i = 0; i < 4; i++) localStorage.removeItem('aigirls_save_v1_' + i);
    })()""")
    pg.goto(BASE + "/game.html")
    pg.wait_for_timeout(800)
    if pg.evaluate("!localStorage.getItem('aigirls_name')"):
        pg.fill("#nameInput", "存档测试玩家")
        pg.click("#nameOk")
        pg.wait_for_timeout(600)

    # ── 0. 列出所有小游戏位置 ──
    mgs = pg.evaluate("""(() => {
      const out = [];
      STORY.forEach((s, si) => s.lines.forEach((l, li) => {
        if (l.t === 'minigame') out.push({ si, li, title: l.title || '', date: l.date || '' });
      }));
      return out;
    })()""")
    print(f"发现小游戏 {len(mgs)} 个: {[(m['si'], m['li'], m['title']) for m in mgs]}")
    if len(mgs) != 3:
        print("!! 小游戏数量异常，期望 3 个"); sys.exit(1)
    check("共 3 个小游戏", len(mgs) == 3)

    # ── 1. 点击开始 ──
    pg.click("#titleCard"); pg.wait_for_timeout(500)

    saved = []  # 记录每档的 (si, li) 存档点（引擎语义：lineIdx=li 时当前显示小游戏前一行）
    for idx, mg in enumerate(mgs):
        si, li = mg["si"], mg["li"]
        slot_i = SLOT_MAP[idx + 1]

        # ── 推进剧情到 lineIdx=li（当前显示小游戏前一行，即存档点）──
        pg.evaluate("""((target) => {
          let guard = 0;
          while (guard++ < 4000) {
            if (sceneIdx === target.si && lineIdx === target.li) return 'ok';
            const cur = STORY[sceneIdx] && STORY[sceneIdx].lines[lineIdx];
            if (!cur) { next(); continue; }                                 // 场景结尾 → 引擎切下一幕
            if (typing) { clearInterval(window.__iv); typing = false; continue; } // 打完当前行
            if (cur.t === 'minigame') { lineIdx++; continue; }                    // 之前的小游戏行顺延
            if (cur.t === 'transition') { lineIdx++; continue; }                  // 过渡行直接过
            if (cur.t === 'choice') {                                             // next() 渲染选项再点第一项
              next();
              const btn = document.querySelector('#choices button');
              if (btn) btn.click();
              continue;
            }
            next();
          }
          return 'guard';
        })""", {"si": si, "li": li})
        pg.wait_for_timeout(400)

        # 确认已到存档点（lineIdx=li → 当前显示 li-1 = 小游戏前一行）
        at = pg.evaluate("(sceneIdx === %d && lineIdx === %d)" % (si, li))
        if not at:
            pos = pg.evaluate("[sceneIdx, lineIdx]")
            print(f"!! 未到达存档点: 期望 [{si},{li}] 实际 {pos}")
            sys.exit(1)
        before_text = pg.evaluate("STORY[%d].lines[%d].text" % (si, li - 1))
        print(f"\n── 小游戏 {idx+1}「{mg['title']}」 存档点 [{si},{li-1}] 行文本: {before_text[:26]}…")

        # ── 真实玩家操作：菜单 →「存档」→ 点槽位 → 关闭 → 收起菜单 ──
        pg.click("#menuBtn"); pg.wait_for_timeout(300)
        pg.click("#mSave"); pg.wait_for_timeout(300)
        check(f"存档面板打开 (小游戏{idx+1})", pg.is_visible("#savePanel"))
        pg.click(f"#slots .slot[data-i='{slot_i}']"); pg.wait_for_timeout(400)
        check(f"槽位 {idx+1} 已保存", pg.evaluate("!!localStorage.getItem('aigirls_save_v1_%d')" % slot_i))
        pg.click("#saveClose"); pg.wait_for_timeout(300)
        pg.click("#menuBtn"); pg.wait_for_timeout(300)

        # ── 跳过小游戏行，继续推进到下一个 ──
        pg.evaluate("lineIdx++")
        saved.append({"si": si, "li": li, "slot": slot_i, "title": mg["title"]})

    # ── 2. 验证 3 个存档 JSON 内容 ──
    print("\n═══ 存档内容验证 ═══")
    for s in saved:
        raw = pg.evaluate("localStorage.getItem('aigirls_save_v1_%d')" % s["slot"])
        d = json.loads(raw)
        # 存档存「当前显示行」= lineIdx-1 = 小游戏前一行
        ok = (d["scene"] == s["si"] and d["line"] == s["li"] - 1)
        check(f"槽位 {s['slot']+1}「{s['title']}」scene/line 正确", ok,
              f"→ [{d['scene']},{d['line']}] t={d['t']}")
        check(f"槽位 {s['slot']+1} 行文本一致", d["line"] == s["li"] - 1 and pg.evaluate(
            "STORY[%d].lines[%d].text" % (d["scene"], d["line"])) == pg.evaluate(
            "STORY[%d].lines[%d].text" % (s["si"], s["li"] - 1)), "「%s…」" % pg.evaluate(
            "STORY[%d].lines[%d].text" % (s["si"], s["li"] - 1))[:18])

    # ── 3. 读档验证：回到开头，真实点「读档」逐槽读取 ──
    print("\n═══ 读档验证 ═══")
    pg.evaluate("location.reload()"); pg.wait_for_timeout(1000)
    if pg.evaluate("!localStorage.getItem('aigirls_name')"):
        pg.fill("#nameInput", "存档测试玩家"); pg.click("#nameOk"); pg.wait_for_timeout(500)
    # 若回到标题卡则点击开始（reload 后可能停在标题）
    if pg.evaluate("document.getElementById('titleCard').style.display !== 'none'"):
        pg.click("#titleCard"); pg.wait_for_timeout(500)
    for s in saved:
        pg.click("#menuBtn"); pg.wait_for_timeout(300)
        pg.click("#mLoad"); pg.wait_for_timeout(300)
        check(f"读档面板打开 (槽位 {s['slot']+1})", pg.is_visible("#savePanel"))
        pg.click(f"#slots .slot[data-i='{s['slot']}']")
        pg.wait_for_timeout(400)
        pg.click("#menuBtn"); pg.wait_for_timeout(300)

        # 读档后显示存档点文本（dataset.full 不受打字进度影响）
        shown = pg.evaluate("document.getElementById('text').dataset.full || document.getElementById('text').textContent")
        expect = pg.evaluate("STORY[%d].lines[%d].text" % (s["si"], s["li"] - 1))
        norm = lambda t: t.replace("{PC}", "").replace("陈默", "存档测试玩家").replace("\n", "")
        check(f"槽位 {s['slot']+1} 读档后文本正确", norm(shown).strip() == norm(expect).strip(),
              f"「{shown[:18]}…」")

        # 点击推进到小游戏：打字中点一下=显示全文，再点=推进（真实玩家行为）
        pg.click("#boxInner"); pg.wait_for_timeout(400)
        if not pg.is_visible("#mgIntro"):
            pg.click("#boxInner"); pg.wait_for_timeout(600)
        intro = pg.is_visible("#mgIntro")
        check(f"槽位 {s['slot']+1} 读档后到达小游戏「{s['title']}」", intro,
              pg.evaluate("document.getElementById('mgIntroT')?.textContent || ''")[:14] if intro else "")
        # 关闭小游戏开场（Esc 等价操作），回到剧情继续下一槽
        pg.evaluate("""(() => { if (typeof MG_LINE !== 'undefined' && MG_LINE && closeMgFrame) closeMgFrame(MG_LINE); })()""")
        pg.wait_for_timeout(300)

    b.close()

print(f"\n══════ 结果: {PASS} 通过 / {FAIL} 失败 ══════")
sys.exit(1 if FAIL else 0)
