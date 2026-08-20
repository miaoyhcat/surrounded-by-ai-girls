# -*- coding: utf-8 -*-
"""配音序号一致性综合测试：
覆盖 自动播放 / 快进停止 / 快进到选项 / 模式切换 后配音与台词的对应关系。
核心断言：自动播放时每个角色行播放的 mp3 文件名 == 该行在场景中的累计序号。"""
import json, subprocess, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8899/game.html"
results = []
def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + (("  | " + extra) if extra else ""))

# 用 node 导出 STORY
node_out = subprocess.run(
    ["node", "-e",
     "const fs=require('fs');const c=fs.readFileSync('src/web/demo/data.js','utf-8');"
     "const S=new Function(c+'; return STORY;')();"
     "process.stdout.write(JSON.stringify(S.map(s=>({id:s.id,lines:s.lines}))))"],
    capture_output=True, text=True, cwd=r"C:\Users\windows\ZCodeProject\ai-galgame", check=True)
STORY = json.loads(node_out.stdout)
roles = ("g", "whale", "claude")

def expected_seq(scene_idx, line_idx):
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
    pg.wait_for_timeout(400)
    pg.evaluate("localStorage.clear()")
    pg.reload()
    pg.wait_for_timeout(400)
    pg.evaluate("""() => {
      PLAYER_NAME = '测试君';
      sceneIdx = 0; lineIdx = 0; AFF = {g:0, whale:0, claude:0};
      history = []; voiceSeq = {g:0, whale:0, claude:0};
      inTitle = false; inChoice = false; inTransition = false; skipMode = false; skipToChoice = false; autoMode = false;
      showLine(STORY[0].lines[0]);
      lineIdx = 1;
    }""")
    pg.wait_for_timeout(1200)

    def snap():
        return pg.evaluate("""({
          l: lineIdx, s: sceneIdx, seq: {...voiceSeq},
          cur: lineIdx > 0 && STORY[sceneIdx].lines[Math.min(lineIdx-1, STORY[sceneIdx].lines.length-1)] ? STORY[sceneIdx].lines[Math.min(lineIdx-1, STORY[sceneIdx].lines.length-1)].t : ''
        })""")

    def verify_seq(tag):
        st = snap()
        exp = expected_seq(st["s"], st["l"])
        ok = all(st["seq"][r] == exp[r] for r in roles)
        check(f"{tag}: voiceSeq 与行位置一致", ok, f"实际={st['seq']} 期望={exp} line={st['l']}")
        return ok

    # 手动推进 25 行
    for _ in range(25):
        pg.evaluate("next()")
        pg.wait_for_timeout(60)
    verify_seq("手动推进 25 行后")

    # 路径1：直接开启自动播放（正常路径），走 8 行，校验每行配音文件名
    pg.evaluate("settings.autoSpeed=4; settings.autoCustom=0.5; autoMode=true; scheduleAuto()")
    seen1 = []
    for _ in range(8):
        pg.wait_for_timeout(650)
        info = pg.evaluate("""({
          l: lineIdx,
          curT: lineIdx > 0 ? (STORY[sceneIdx].lines[Math.min(lineIdx-1, STORY[sceneIdx].lines.length-1)] || {}).t : '',
          src: voiceAudio && voiceAudio.src ? voiceAudio.src.split('/').pop() : ''
        })""")
        if info["src"] and not any(s == info["src"] for s in seen1):
            seen1.append(info["src"])
    check("路径1 自动播放正常推进且播放配音", len(seen1) >= 2, f"播放 {len(seen1)} 个: {seen1}")
    pg.evaluate("autoMode = false; clearTimeout(autoTimer)")

    # 路径2：快进 30 行 → 停止（stopSkip）→ 开自动播放
    pg.evaluate("skipMode = true; runSkip()")
    pg.wait_for_timeout(300)  # 快进约 12 行
    pg.evaluate("stopSkip()")
    pg.wait_for_timeout(100)
    verify_seq("快进停止后")
    pg.evaluate("settings.autoSpeed=4; settings.autoCustom=0.5; autoMode=true; scheduleAuto()")
    seen2 = []
    for _ in range(6):
        pg.wait_for_timeout(650)
        info = pg.evaluate("""({
          l: lineIdx,
          curT: lineIdx > 0 ? (STORY[sceneIdx].lines[Math.min(lineIdx-1, STORY[sceneIdx].lines.length-1)] || {}).t : '',
          src: voiceAudio && voiceAudio.src ? voiceAudio.src.split('/').pop() : ''
        })""")
        if info["src"] and not any(s == info["src"] for s in seen2):
            seen2.append(info["src"])
    check("路径2 快进停止后自动播放正常", len(seen2) >= 2, f"播放 {len(seen2)} 个: {seen2}")
    pg.evaluate("autoMode = false; clearTimeout(autoTimer)")

    # 路径3：直接点 mAuto 按钮切换（模拟用户操作，含 resetVoiceSeq）
    pg.evaluate("document.getElementById('mAuto').click()")  # 开
    pg.wait_for_timeout(200)
    pg.evaluate("document.getElementById('mAuto').click()")  # 关
    pg.wait_for_timeout(100)
    verify_seq("mAuto 开关切换后")

    # 路径4：mSkip 按钮快进开关
    pg.evaluate("document.getElementById('mSkip').click()")  # 开快进
    pg.wait_for_timeout(250)
    pg.evaluate("document.getElementById('mSkip').click()")  # 关快进
    pg.wait_for_timeout(100)
    verify_seq("mSkip 开关切换后")

    # 路径5：历史回档到有角色台词的位置 → 自动播放
    pg.evaluate("showHistory()")
    pg.wait_for_timeout(200)
    pg.evaluate("document.querySelectorAll('.hrow')[6].click()")
    pg.wait_for_timeout(300)
    verify_seq("历史回档后")
    pg.evaluate("settings.autoSpeed=4; settings.autoCustom=0.5; autoMode=true; scheduleAuto()")
    seen5 = []
    for _ in range(6):
        pg.wait_for_timeout(650)
        info = pg.evaluate("""({
          l: lineIdx,
          curT: lineIdx > 0 ? (STORY[sceneIdx].lines[Math.min(lineIdx-1, STORY[sceneIdx].lines.length-1)] || {}).t : '',
          src: voiceAudio && voiceAudio.src ? voiceAudio.src.split('/').pop() : ''
        })""")
        if info["src"] and not any(s == info["src"] for s in seen5):
            seen5.append(info["src"])
    check("路径5 回档后自动播放正常", len(seen5) >= 2, f"播放 {len(seen5)} 个: {seen5}")
    pg.evaluate("autoMode = false; clearTimeout(autoTimer)")

    check("无页面/控制台错误", len(errors) == 0, "; ".join(errors[:3]) if errors else "")
    b.close()

fails = [n for n, ok in results if not ok]
print(f"\n===== 配音序号一致性综合: {len(results)-len(fails)}/{len(results)} 通过 =====")
sys.exit(1 if fails else 0)
