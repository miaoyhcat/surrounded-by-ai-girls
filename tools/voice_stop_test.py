# -*- coding: utf-8 -*-
"""配音停止/无重叠测试（当前引擎版）：
验证：连续快速推进多句台词，任何时刻最多只有一个 voiceAudio 在播。
（playVoice 先 stopVoice 再播新句——杜绝重叠）"""
import sys
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

    # 进入 s4（含 whale 角色），先播一句 whale
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
    pg.wait_for_timeout(2000)  # whale 配音开始播放

    # 断言 1：whale 配音在播
    st1 = pg.evaluate("voiceAudio ? {src: voiceAudio.src.split('/').pop(), paused: voiceAudio.paused} : null")
    check("whale 配音正在播放", st1 and not st1["paused"] and "whale" in st1["src"], str(st1))

    # 断言 2：立即切到 g 台词（whale 还没念完），旧配音必须被停止
    pg.evaluate("""() => {
      const si = sceneIdx;
      while(lineIdx < STORY[si].lines.length && STORY[si].lines[lineIdx].t !== 'g') lineIdx++;
      showLine(STORY[si].lines[lineIdx]); lineIdx++;
    }""")
    pg.wait_for_timeout(800)
    st2 = pg.evaluate("voiceAudio ? {src: voiceAudio.src.split('/').pop(), paused: voiceAudio.paused, dur: Math.round(voiceAudio.duration)} : null")
    check("切换到 g 台词（新配音在播）", st2 and not st2["paused"] and "g_" in st2["src"], str(st2))

    # 断言 3：快速连播 8 句，任何时刻只有一个声音源（每次切换旧声被停）
    overlap = False
    for i in range(8):
        pg.evaluate("""() => {
          const si = sceneIdx;
          if(lineIdx >= STORY[si].lines.length){ sceneIdx = si+1; lineIdx = 0; }
          const s = STORY[sceneIdx];
          if(lineIdx < s.lines.length && (s.lines[lineIdx].t === 'g' || s.lines[lineIdx].t === 'whale' || s.lines[lineIdx].t === 'claude')){
            showLine(s.lines[lineIdx]); lineIdx++;
          }
        }""")
        pg.wait_for_timeout(120)
        st = pg.evaluate("""(() => {
          const audios = document.querySelectorAll('audio');
          const playing = [];
          audios.forEach(a => { if(!a.paused) playing.push(a.src.split('/').pop()); });
          return playing;
        })()""")
        if len(st) > 1:
            overlap = True
            print(f"  第{i}句 重叠! 同时播放: {st}")
    check("快速连播无重叠（任一时刻单一声源）", not overlap)

    # 断言 4：stopVoice 后清空
    pg.evaluate("stopVoice()")
    st3 = pg.evaluate("voiceAudio === null")
    check("stopVoice 清空当前配音", st3)

    check("无页面/控制台错误", len(errors) == 0, "; ".join(errors[:3]) if errors else "")
    b.close()

fails = [n for n, ok in results if not ok]
print(f"\n===== 配音停止/无重叠: {len(results)-len(fails)}/{len(results)} 通过 =====")
sys.exit(1 if fails else 0)
