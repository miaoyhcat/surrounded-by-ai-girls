# -*- coding: utf-8 -*-
"""从 data.js 提取完整剧本 → docs/story_full_v5.md"""
import re, sys
sys.path.insert(0, ".")
src = open("data.js", encoding="utf-8").read()
# 提取 STORY 数组（粗略：用 vm 执行最稳）
import subprocess, json, os
js = """
const fs = require('fs'); const vm = require('vm');
let code = fs.readFileSync('data.js','utf8');
code = code.replace(/^(const|let)\s+(STORY|ENDINGS|AFF)\b/gm, 'var $2');
const sandbox = {}; vm.createContext(sandbox); vm.runInContext(code, sandbox);
process.stdout.write(JSON.stringify({story: sandbox.STORY, endings: sandbox.ENDINGS}));
"""
r = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=os.getcwd())
d = json.loads(r.stdout)
STORY, ENDINGS = d["story"], d["endings"]

SPK = {"narr":"【旁白】", "you":"你", "g":"GPT娘", "whale":"鲸鱼娘", "claude":"claude娘", "oclaw":"OpenClaw"}
out = ["# 《完蛋，我被AI娘包围了》完整剧情 v5（全CG对应版）", "",
       "> 2026-08-11 · v5：10 幕 851 行 · 预计 120 分钟 · 每张 CG 剧情 ≥10 分钟", ""]
for i, s in enumerate(STORY, 1):
    out.append(f"╔══════════════ 幕 {i} · {s['title']} ══════════════")
    out.append(f"║ 时间：{s['date']}  |  CG：{s['cg'].split('/')[-1]}")
    out.append("╚════════════════════════════════════════")
    out.append("")
    for l in s["lines"]:
        if l["t"] == "transition":
            out.append(f"◆ 转场（{l.get('date','')}）：{l['text']}")
            out.append("")
        elif l["t"] == "choice":
            out.append(f"◇ 选项：{l['text']}")
            for ch in l["choices"]:
                rp = ch["reply"]
                tag = f"+{ch.get('affect','')}" if ch.get("affect") else ""
                out.append(f"   · {ch['label']} → {SPK.get(rp['t'],rp['t'])}：{rp['text']} {tag}")
            out.append("")
        else:
            out.append(f"{SPK.get(l['t'], l['t'])}：{l['text']}")
    out.append("")

# 结局
out.append("═══ 结 局 ═══")
for k, e in ENDINGS.items():
    out.append(f"\n【{k}】{e['title']}")
    out.append(e["text"])

doc = "\n".join(out)
os.makedirs(os.path.join(os.path.dirname(os.getcwd()), "docs"), exist_ok=True)
outpath = os.path.join(os.path.dirname(os.getcwd()), "docs", "story_full_v5.md")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(doc)
print("saved:", outpath, len(doc), "chars")
