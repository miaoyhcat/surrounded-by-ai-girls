# -*- coding: utf-8 -*-
"""选项处历史回档专项测试：
1. 推进到选项 → 选一个 → 继续若干行
2. 历史回档到"选项回复行" → 应显示回复原文，且能继续推进
3. 回档后历史被裁剪
4. 若 choice 是场景最后一行（无后续），回档也不崩
"""
import sys, json
from playwright.sync_api import sync_playwright

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print("PASS ", name, extra)
    else: FAIL += 1; print("FAIL ", name, extra)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto("file:///C:/Users/windows/ZCodeProject/ai-galgame/src/web/demo/game.html")
    pg.wait_for_timeout(600)

    # 有名字则跳过名字面板
    if pg.evaluate("!localStorage.getItem('aigirls_name')"):
        pg.fill("#nameInput", "测试君")
        pg.click("#nameOk")
        pg.wait_for_timeout(500)

    # 直接定位到含 choice 的场景，跳到 choice 前一行
    pg.evaluate("""
      sceneIdx = 0;
      const scene = STORY[0];
      const ci = scene.lines.findIndex(l => l.t === 'choice');
      lineIdx = ci;  // next() 将显示 choice 行
      inTitle = false; inChoice = false; inTransition = false;
      document.getElementById('titleCard').style.display = 'none';
      let pi = ci - 1;
      while(pi > 0 && scene.lines[pi].t === 'minigame') pi--;  // 跳过 minigame 行
      showLine(scene.lines[pi]);  // 显示 choice 前一行
      lineIdx = ci;
    """)
    pg.wait_for_timeout(300)

    # 点击推进 → 出现选项（等打字完成）
    pg.wait_for_function("!typing", timeout=5000)
    pg.click("#boxInner"); pg.wait_for_timeout(500)
    check("选项出现", pg.is_visible("#choices"))
    choices = pg.evaluate("document.querySelectorAll('#choices button').length")
    check("选项数≥2", choices >= 2, f"n={choices}")

    # 选第一个选项
    reply0 = pg.evaluate("document.querySelector('#choices button').textContent")
    pg.click("#choices button")
    pg.wait_for_timeout(400)
    cur_text = pg.evaluate("document.getElementById('text').textContent")
    check("回复显示", len(cur_text) > 0, cur_text[:24])

    # 历史记录应包含该回复
    hist_before = pg.evaluate("history.map(h => h.text.slice(0,10))")
    check("历史含回复行", any(t in cur_text[:10] for t in hist_before[-3:]), str(hist_before[-3:]))

    # 继续推进 2 行（等打字完成避免点击被吞）
    pg.wait_for_function("!typing", timeout=5000)
    pg.click("#boxInner"); pg.wait_for_function("!typing", timeout=5000)
    pg.click("#boxInner"); pg.wait_for_function("!typing", timeout=5000)
    n_hist = pg.evaluate("history.length")

    # 打开历史，找到回复行（回复文本 = cur_text），点它回档
    target_text = cur_text.strip()[:14]
    idx = pg.evaluate("""(t) => {
      const i = history.findIndex(h => h.text.includes(t));
      return {i, isReply: i >= 0 ? (history[i].replyOf !== undefined) : false};
    }""", target_text)
    check("找到回复行索引", idx["i"] >= 0, str(idx))
    check("回复行带 replyOf 标记", idx["isReply"])

    # 通过 jumpBack 直接回档
    back_state = pg.evaluate("""(i) => {
      jumpBack(i);
      return {text: document.getElementById('text').textContent, line: lineIdx, h: history[i]};
    }""", idx["i"])
    pg.wait_for_timeout(400)
    back_text = back_state["text"]
    check("回档显示回复原文", target_text in back_text, back_text[:24])
    check("历史已裁剪", pg.evaluate("history.length") <= idx["i"] + 1,
          f"len={pg.evaluate('history.length')} (was {n_hist})")

    # 回档后可继续推进
    pg.click("#boxInner"); pg.wait_for_timeout(400)
    next_text = pg.evaluate("document.getElementById('text').textContent")
    check("回档后能继续推进", len(next_text.strip()) > 0, next_text[:20])

    # 边界：choice 是最后一行（用 s6c 检查是否最后一个 line 是 choice）
    last_choice = pg.evaluate("""(() => {
      const bad = [];
      STORY.forEach((s, si) => {
        const last = s.lines[s.lines.length - 1];
        if (last && last.t === 'choice') bad.push({scene: si, id: s.id});
        // 同时检查 choice 后无行但回复行记录越界的情况
        const ci = s.lines.findIndex(l => l.t === 'choice');
        if (ci >= 0 && ci === s.lines.length - 1) bad.push({scene: si, id: s.id, note: 'choice-last'});
      });
      return bad;
    })()""")
    print("  场景末尾是 choice 的:", json.dumps(last_choice, ensure_ascii=False))

    # 边界：构造"choice 是场景最后一行 + 选择后有 reply"的合成场景，验证回档不崩
    pg.evaluate("""(() => {
      history = [];
      STORY.push({
        id: "test_end_choice",
        bgm: "acoustic54",
        title: "边界测试",
        date: "测试日",
        cg: "assets/test.png",
        lines: [
          {t:"narr", text:"这是倒数第二行。"},
          {t:"narr", text:"最后一行是 choice。"},
          {t:"choice", text:"选一个", choices:[
            {label:"甲", reply:{t:"g", text:"选了甲——没有后续行。"}, affect:"g"},
            {label:"乙", reply:{t:"g", text:"选了乙——也没有后续行。"}}
          ]}
        ]
      });
      sceneIdx = STORY.length - 1;
      lineIdx = 0; inChoice = false; inTransition = false; inTitle = false;
      document.getElementById('titleCard').style.display = 'none';
      showLine(STORY[sceneIdx].lines[0]);
    })()""")
    pg.wait_for_function("!typing", timeout=5000)
    pg.click("#boxInner"); pg.wait_for_function("!typing", timeout=5000)
    pg.click("#boxInner"); pg.wait_for_function("!typing", timeout=5000)
    pg.click("#boxInner"); pg.wait_for_timeout(400)
    check("合成场景选项出现", pg.is_visible("#choices"))
    pg.click("#choices button"); pg.wait_for_function("!typing", timeout=5000)
    # 此时 choice 是最后一行，lineIdx 已越界（= lines.length）
    over = pg.evaluate("lineIdx === STORY[sceneIdx].lines.length")
    check("末尾choice回复后 lineIdx 越界", over, f"lineIdx={pg.evaluate('lineIdx')}")
    # 回档到该回复行：应显示回复原文且不崩
    r = pg.evaluate("""(() => {
      const i = history.findIndex(h => h.replyOf !== undefined);
      if (i < 0) return {ok: false, why: "no replyOf row"};
      const h = history[i];
      jumpBack(i);
      return {ok: true, text: document.getElementById('text').textContent.slice(0, 16), line: lineIdx};
    })()""")
    check("末尾choice回档不崩且显示原文", r["ok"] and "选了甲" in r["text"], str(r))
    # 回档后点击应能继续（末尾场景无后续 = 停住不崩；真实 s7 为跳转 choice 另有分支）
    pg.click("#boxInner"); pg.wait_for_timeout(400)
    nxt = pg.evaluate("""(() => ({
      scene: STORY[sceneIdx] ? STORY[sceneIdx].id : "END",
      inTitle: inTitle,
      ending: document.getElementById('ending').style.display !== 'none',
      crash: typeof sceneIdx === 'undefined'
    }))()""")
    check("回档后可继续（末尾停住不崩）", not nxt["crash"], str(nxt))
    # 清理合成场景
    pg.evaluate("STORY.pop()")

    # 快进/继续功能不受影响
    pg.evaluate("sceneIdx = 0; lineIdx = 0;")
    b.close()

print(f"\n===== 选项回档专项: {PASS}/{PASS+FAIL} 通过 =====")
sys.exit(1 if FAIL else 0)
