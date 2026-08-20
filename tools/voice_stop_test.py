# -*- coding: utf-8 -*-
"""配音停止/无重叠测试：
模拟专业引擎行为——每句新台词开始前强制停掉旧配音（Ren'Py voice_can_be_suppressed 同款）。
验证：连续快速推进多句（含 whale 变声句），任何时刻最多只有一个声音源在播。"""
import json, subprocess, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8899/game.html"
results = []
def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + (("  | " + extra) if extra else ""))

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    errors = []
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(BASE)
    pg.wait_for_timeout(400)
    pg.evaluate("localStorage.clear()")
    pg.reload()
    pg.wait_for_timeout(400)

    # 进入 s4（含 whale），先播一句 whale（变声路径）
    pg.evaluate("""() => {
      PLAYER_NAME='测试君';
      const si = STORY.findIndex(s => s.id === 's4');
      sceneIdx = si; lineIdx = 0; AFF = {g:0,whale:0,claude:0};
      history = []; voiceSeq = {g:0,whale:0,claude:0};
      inTitle=false; inChoice=false; inTransition=false; skipMode=false;
      document.getElementById('namePanel').style.display='none';
      while(lineIdx < STORY[si].lines.length && STORY[si].lines[lineIdx].t !== 'whale') lineIdx++;
      showLine(STORY[si].lines[lineIdx]); lineIdx++;
    }""")
    pg.wait_for_timeout(2000)  # whale 变声开始播放

    # 关键断言 1：whale 变声在播（voiceShifter 存在）
    has_shifter = pg.evaluate("voiceShifter !== null")
    check("whale 变声正在播放（voiceShifter 存在）", has_shifter)

    # 关键断言 2：立即切到 g 台词（whale 台词还没念完），旧配音必须被停止
    pg.evaluate("""() => {
      const si = sceneIdx;
      while(lineIdx < STORY[si].lines.length && STORY[si].lines[lineIdx].t !== 'g') lineIdx++;
      showLine(STORY[si].lines[lineIdx]); lineIdx++;
    }""")
    pg.wait_for_timeout(800)
    st = pg.evaluate("""({
      shifter: voiceShifter !== null,
      chain: voiceChain.length,
      audio: voiceAudio ? (typeof voiceAudio.pause === 'function' ? 'htmlaudio' : typeof voiceAudio.connect === 'function' ? 'scriptnode' : 'other') : 'none'
    })""")
    print("切换后状态:", st)
    check("whale 变声已被停止（voiceShifter 清空）", not st["shifter"] and st["chain"] == 0,
          f"shifter={st['shifter']} chain={st['chain']}")
    check("g 台词正在播（HTMLAudio）", st["audio"] == "htmlaudio", st["audio"])

    # 关键断言 3：快速连播 5 句（模拟自动播放节奏），每次切换旧声都被停
    ok_all = True
    for i in range(5):
        pg.evaluate("""() => {
          const si = sceneIdx;
          if(lineIdx >= STORY[si].lines.length){ si2 = si+1; sceneIdx = si2; lineIdx = 0; }
          showLine(STORY[si===undefined?sceneIdx:si].lines[lineIdx]); lineIdx++;
        }""")
        pg.wait_for_timeout(150)
        st2 = pg.evaluate("""({
          shifter: voiceShifter !== null,
          chain: voiceChain.length,
          audio: voiceAudio ? (typeof voiceAudio.pause === 'function' ? 'htmlaudio' : 'scriptnode') : 'none',
          gen: voiceGen
        })""")
        # 任何时刻：要么 HTMLAudio 在播，要么 ScriptNode 在播，要么无；但不能同时有两个
        if st2["shifter"] and st2["audio"] == "htmlaudio":
            ok_all = False
            print(f"  第{i}句 重叠! shifter={st2['shifter']} audio={st2['audio']}")
    check("快速连播无重叠（任一时刻单一声源）", ok_all)

    # 关键断言 4：stopVoice 后一切清空
    pg.evaluate("showLine(STORY[sceneIdx].lines[Math.min(lineIdx, STORY[sceneIdx].lines.length-1)]); lineIdx++;")
    pg.wait_for_timeout(300)
    pg.evaluate("stopVoice()")
    st3 = pg.evaluate("({shifter: voiceShifter !== null, chain: voiceChain.length, audio: voiceAudio !== null})")
    check("stopVoice 全部清空", not st3["shifter"] and st3["chain"] == 0 and not st3["audio"], str(st3))

    check("无页面/控制台错误", len(errors) == 0, "; ".join(errors[:3]) if errors else "")
    b.close()

fails = [n for n, ok in results if not ok]
print(f"\n===== 配音停止/无重叠: {len(results)-len(fails)}/{len(results)} 通过 =====")
sys.exit(1 if fails else 0)
