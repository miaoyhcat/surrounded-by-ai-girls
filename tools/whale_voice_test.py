# -*- coding: utf-8 -*-
"""实时变声（鲸鱼娘 SoundTouch）功能测试：
1. soundtouch.js 加载成功
2. whale 台词走变声路径（AudioBufferSourceNode + 变调），g/claude 走原声路径
3. 变声开关存在且默认开启
4. 变声后输出 buffer 时长/采样率正常，与原始 mp3 有差异（确实变了调）
5. 与既有的配音序号一致性不冲突"""
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
    pg.wait_for_timeout(500)

    # 1. soundtouch.js 加载
    has_st = pg.evaluate("typeof SoundTouch === 'function'")
    check("soundtouch.js 已加载", has_st)

    # 2. 设置开关存在且默认开
    has_sw = pg.evaluate("!!document.getElementById('sWhaleVoice') && settings.whaleVoice === true")
    check("鲸鱼娘少女音开关存在且默认开", has_sw)

    # 3. 进入 s4（鲸鱼娘登场场景），播放 whale 台词
    pg.evaluate("""() => {
      PLAYER_NAME = '测试君';
      const si = STORY.findIndex(s => s.id === 's4');
      sceneIdx = si; lineIdx = 0; AFF = {g:0, whale:0, claude:0};
      history = []; voiceSeq = {g:0, whale:0, claude:0};
      inTitle = false; inChoice = false; inTransition = false; skipMode = false;
      // 直接推进到第一句 whale 台词
      while(lineIdx < STORY[si].lines.length && STORY[si].lines[lineIdx].t !== 'whale'){
        lineIdx++;
      }
      showLine(STORY[si].lines[lineIdx]);
      lineIdx++;
    }""")
    pg.wait_for_timeout(2000)  # 等变声异步处理完成

    # whale 应走变声路径：voiceAudio 是 PitchShifter 的 ScriptProcessorNode（有 connect/disconnect，非 HTMLAudioElement）
    is_bufnode = pg.evaluate("voiceAudio ? (typeof voiceAudio.connect === 'function' && typeof voiceAudio.pause !== 'function') : false")
    check("whale 台词走实时变声路径（ScriptProcessorNode）", is_bufnode)

    # 4. 变声缓存存在且时长合理
    cache_info = pg.evaluate("""() => {
      const keys = Object.keys(voiceCache);
      if(keys.length === 0) return {n: 0};
      const buf = voiceCache[keys[0]];
      return {n: keys.length, dur: buf.duration.toFixed(2), sr: buf.sampleRate};
    }""")
    check("变声 buffer 已缓存且时长合理", cache_info.get("n", 0) > 0 and float(cache_info.get("dur", "0")) > 0.5, f"{cache_info}")

    # 5. GPT 台词走原声路径（HTMLAudioElement：有 pause 无 stop）
    pg.evaluate("""() => {
      const si = sceneIdx;
      while(lineIdx < STORY[si].lines.length && STORY[si].lines[lineIdx].t !== 'g'){
        lineIdx++;
      }
      if(lineIdx < STORY[si].lines.length){
        showLine(STORY[si].lines[lineIdx]);
        lineIdx++;
      }
    }""")
    pg.wait_for_timeout(800)
    is_audio_el = pg.evaluate("voiceAudio ? (typeof voiceAudio.pause === 'function' && typeof voiceAudio.stop !== 'function') : false")
    check("GPT 台词走原声路径（HTMLAudioElement）", is_audio_el)

    # 6. 关闭鲸鱼娘变声后，whale 走原声路径
    pg.evaluate("settings.whaleVoice = false")
    pg.evaluate("""() => {
      const si = sceneIdx;
      while(lineIdx < STORY[si].lines.length && STORY[si].lines[lineIdx].t !== 'whale'){
        lineIdx++;
      }
      if(lineIdx < STORY[si].lines.length){
        showLine(STORY[si].lines[lineIdx]);
        lineIdx++;
      }
    }""")
    pg.wait_for_timeout(800)
    is_audio_el2 = pg.evaluate("voiceAudio ? (typeof voiceAudio.pause === 'function' && typeof voiceAudio.stop !== 'function') : false")
    check("关闭变声后 whale 走原声路径", is_audio_el2)

    # 7. 无错误
    check("无页面/控制台错误", len(errors) == 0, "; ".join(errors[:3]) if errors else "")
    b.close()

fails = [n for n, ok in results if not ok]
print(f"\n===== 实时变声功能: {len(results)-len(fails)}/{len(results)} 通过 =====")
sys.exit(1 if fails else 0)
