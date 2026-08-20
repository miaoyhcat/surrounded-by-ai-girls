# -*- coding: utf-8 -*-
"""历史回档 + 自动播放 配音序号一致性测试
复现用户 bug：回档到过去剧情后自动播放，声音与台词各说各的。
验证：回档后 voiceSeq 重建正确，自动播放每行请求的 mp3 序号与该行台词一一对应。"""
import json, re, os, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8899/game.html"
results = []
def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + (("  | " + extra) if extra else ""))

# 从 data.js 提取场景台词顺序（与游戏一致：跳过 reply）——data.js 非标准 JSON，用 node 导出
import subprocess
node_out = subprocess.run(
    ["node", "-e",
     "const fs=require('fs');const c=fs.readFileSync('src/web/demo/data.js','utf-8');"
     "const S=new Function(c+'; return STORY;')();"
     "process.stdout.write(JSON.stringify(S.map(s=>({id:s.id,lines:s.lines}))))"],
    capture_output=True, text=True, cwd=r"C:\Users\windows\ZCodeProject\ai-galgame", check=True)
STORY = json.loads(node_out.stdout)
roles = ("g", "whale", "claude")

def expected_seq(scene_idx, line_idx):
    """游戏内 resetVoiceSeq 的正确语义：数 lines[0..line_idx-1] 的角色行"""
    seq = {"g": 0, "whale": 0, "claude": 0}
    for l in STORY[scene_idx]["lines"][:line_idx]:
        if l.get("t") in roles:
            seq[l["t"]] += 1
    return seq

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    errors = []
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(BASE)
    pg.wait_for_timeout(500)
    # 开始新游戏（清存档，直接调用内部流程，避免 UI 点击时序）
    pg.evaluate("localStorage.clear()")
    pg.reload()
    pg.wait_for_timeout(500)
    pg.evaluate("""() => {
      // 跳过名字面板直接开始（与真实流程一致：设置 PLAYER_NAME 并进入第一行）
      PLAYER_NAME = '测试君';
      sceneIdx = 0; lineIdx = 0; AFF = {g:0, whale:0, claude:0};
      history = []; voiceSeq = {g:0, whale:0, claude:0};
      inTitle = false; inChoice = false; inTransition = false;
      showLine(STORY[0].lines[0]);
      lineIdx = 1;
    }""")
    pg.wait_for_timeout(1500)

    # 推进剧情到 s1 中部（手动点击若干次，越过 choice 前的行）
    for _ in range(60):
        pg.evaluate("document.getElementById('boxInner').click()")
        pg.wait_for_timeout(120)
    st = pg.evaluate("({s: sceneIdx, l: lineIdx, seq: {...voiceSeq}})")
    print(f"推进后: scene={st['s']} line={st['l']} voiceSeq={st['seq']}")
    check("推进到 s1 中部", st["s"] == 0 and st["l"] > 20, f"line={st['l']}")

    # 打开历史记录，回档到更早位置（比如 line 15 之前）
    pg.evaluate("showHistory()")
    pg.wait_for_timeout(300)
    # 点击第 10 条历史（较早期）
    pg.evaluate("document.querySelectorAll('.hrow')[10].click()")
    pg.wait_for_timeout(500)
    st2 = pg.evaluate("({s: sceneIdx, l: lineIdx, seq: {...voiceSeq}, hist: history.length})")
    print(f"回档后: scene={st2['s']} line={st2['l']} voiceSeq={st2['seq']}")

    # 关键断言：回档后 voiceSeq 应等于 该场景该行之前的角色计数
    exp = expected_seq(st2["s"], st2["l"])
    seq_ok = all(st2["seq"][r] == exp[r] for r in roles)
    check("回档后 voiceSeq 重建正确", seq_ok, f"实际={st2['seq']} 期望={exp}")

    # 开启自动播放（0.6s 快档），连续走 15 行，记录每次播放的音频 src，与期望序号比对
    pg.evaluate("settings.autoSpeed=4; settings.autoCustom=0.6; autoMode=true; scheduleAuto()")
    seen = []
    for _ in range(15):
        pg.wait_for_timeout(800)
        info = pg.evaluate("""({
          l: lineIdx,
          t: STORY[sceneIdx].lines[Math.min(lineIdx-1, STORY[sceneIdx].lines.length-1)] ? STORY[sceneIdx].lines[Math.min(lineIdx-1, STORY[sceneIdx].lines.length-1)].t : '',
          src: voiceAudio ? voiceAudio.src.split('/').pop() : '',
          seq: {...voiceSeq}
        })""")
        if info["src"] and info["src"] not in [s for _, _, s, _ in seen]:
            seen.append((info["l"], info["t"], info["src"], info["seq"]))
    # 校验：每个播放的 src 角色序号 == 该行在场景中（跳过 reply）的累计序号
    bad = []
    for l, t, src, seq in seen:
        if t not in roles:
            continue
        # 当前显示行 = lineIdx-1（showLine 后 lineIdx++）
        cur = l - 1
        if cur < 0:
            continue
        # 期望该行累计序号 = 该行前（含自身）角色计数
        cnt = 0
        for ll in STORY[0]["lines"][:cur + 1]:
            if ll.get("t") == t:
                cnt += 1
        fname = f"{t}_{cnt:03d}.mp3"
        if src != fname:
            bad.append((l, t, src, fname))
    print("自动播放 15 行中播放的配音:", [(x[0], x[1], x[2]) for x in seen])
    check("自动播放配音序号与台词一一对应", len(bad) == 0, f"错位 {len(bad)} 个" if bad else f"共 {len(seen)} 个播放")

    # 再次回档验证（回档到 choice 附近再自动播放）
    pg.evaluate("showHistory()")
    pg.wait_for_timeout(300)
    pg.evaluate("document.querySelectorAll('.hrow')[3].click()")
    pg.wait_for_timeout(400)
    st3 = pg.evaluate("({s: sceneIdx, l: lineIdx, seq: {...voiceSeq}})")
    exp3 = expected_seq(st3["s"], st3["l"])
    check("二次回档（更早位置）voiceSeq 正确", all(st3["seq"][r] == exp3[r] for r in roles), f"实际={st3['seq']} 期望={exp3}")

    check("无页面/控制台错误", len(errors) == 0, "; ".join(errors[:3]) if errors else "")
    b.close()

fails = [n for n, ok in results if not ok]
print(f"\n===== 历史回档配音一致性: {len(results)-len(fails)}/{len(results)} 通过 =====")
sys.exit(1 if fails else 0)
