# -*- coding: utf-8 -*-
"""从 data.js 提取完整剧本 → docs/story_full_v5.md"""
import subprocess, json, os

cwd = os.path.dirname(os.path.abspath(__file__))
data_js = os.path.join(os.path.dirname(cwd), "src", "web", "demo", "data.js")
js = r"""
const fs = require('fs'); const vm = require('vm');
let code = fs.readFileSync('__DATA_JS__','utf8');
code = code.replace(/^(const|let)\s+(STORY|ENDINGS|AFF)\b/gm, 'var $2');
const sandbox = {}; vm.createContext(sandbox); vm.runInContext(code, sandbox);
process.stdout.write(JSON.stringify({story: sandbox.STORY, endings: sandbox.ENDINGS}));
""".replace("__DATA_JS__", data_js.replace("\\", "\\\\"))
r = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=cwd)
if r.returncode != 0:
    print("NODE ERR:", r.stderr[:500]); raise SystemExit(1)
d = json.loads(r.stdout)
STORY, ENDINGS = d["story"], d["endings"]

SPK = {"narr": "【旁白】", "you": "你", "g": "GPT娘", "whale": "鲸鱼娘", "claude": "claude娘", "oclaw": "OpenClaw"}
out = ["# 《完蛋，我被AI娘包围了》完整剧情 v5（全CG对应版）", "",
       "> 2026-08-11 · v5：10 幕 851 行 · 预计 120 分钟 · 每张 CG 剧情 ≥10 分钟",
       "> ※ 剧中的「陈默」是占位符——游戏内会替换为你设定的名字（主界面/游戏内均可改名）", ""]
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
                tag = f" [+{ch.get('affect','')}]" if ch.get("affect") else ""
                out.append(f"   · {ch['label']} → {SPK.get(rp['t'], rp['t'])}：{rp['text']}{tag}")
            out.append("")
        else:
            out.append(f"{SPK.get(l['t'], l['t'])}：{l['text']}")
    out.append("")

out.append("═══ 结 局 ═══")
for k, e in ENDINGS.items():
    out.append(f"\n【{k}】{e['title']}")
    out.append(e["text"])

doc = "\n".join(out)
docs_dir = os.path.join(os.path.dirname(cwd), "docs")
os.makedirs(docs_dir, exist_ok=True)
outpath = os.path.join(docs_dir, "story_full_v5.md")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(doc)
print("saved:", outpath, len(doc), "chars")
