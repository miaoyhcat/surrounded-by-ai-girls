# -*- coding: utf-8 -*-
"""生成图文对照版剧本 story_full_v5.html（每幕嵌对应 CG，base64 内嵌单文件）"""
import subprocess, json, os, base64

cwd = os.path.dirname(os.path.abspath(__file__))
demo_dir = os.path.join(os.path.dirname(cwd), "src", "web", "demo")
cg_dir = os.path.join(os.path.dirname(cwd), "assets", "cg")
data_js = os.path.join(demo_dir, "data.js")

js = r"""
const fs = require('fs'); const vm = require('vm');
let code = fs.readFileSync('__DATA_JS__','utf8');
code = code.replace(/^(const|let)\s+(STORY|ENDINGS|AFF)\b/gm, 'var $2');
const sandbox = {}; vm.createContext(sandbox); vm.runInContext(code, sandbox);
process.stdout.write(JSON.stringify({story: sandbox.STORY, endings: sandbox.ENDINGS}));
""".replace("__DATA_JS__", data_js.replace("\\", "\\\\"))
r = subprocess.run(["node", "-e", js], capture_output=True, text=True, cwd=demo_dir)
if r.returncode != 0:
    print("NODE ERR:", r.stderr[:500]); raise SystemExit(1)
d = json.loads(r.stdout)
STORY, ENDINGS = d["story"], d["endings"]

def img_b64(cg_file):
    p = os.path.join(cg_dir, cg_file)
    if not os.path.exists(p):
        p = os.path.join(demo_dir, cg_file)
    if not os.path.exists(p):
        return None
    ext = os.path.splitext(cg_file)[1].lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml"}.get(ext, "image/png")
    with open(p, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()

SPK = {"narr": "【旁白】", "you": "你", "g": "GPT娘", "whale": "鲸鱼娘", "claude": "claude娘", "oclaw": "OpenClaw"}
COLOR = {"narr": "#8B93A7", "you": "#9FB4E8", "g": "#FFD27A", "whale": "#7FB0FF", "claude": "#F0A878", "oclaw": "#A8B8D8"}

parts = []
parts.append("""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>《完蛋，我被AI娘包围了》完整剧情 v5 · 图文对照版</title>
<style>
body{background:#0B1020;color:#E8ECF5;font-family:"Microsoft YaHei","PingFang SC",sans-serif;margin:0;padding:28px 4vw;line-height:2}
h1{text-align:center;letter-spacing:.2em;font-size:26px;color:#FFD27A}
.sub{text-align:center;color:#7D86A0;font-size:13px;letter-spacing:.1em;margin-bottom:40px}
.scene{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:24px 28px;margin-bottom:36px}
.scene h2{color:#FFD27A;font-size:19px;letter-spacing:.12em;margin:0 0 4px}
.scene .meta{color:#7D86A0;font-size:12.5px;letter-spacing:.08em;margin-bottom:14px}
.scene img{display:block;max-width:100%;max-height:420px;border-radius:12px;margin:0 auto 18px;border:1px solid rgba(255,255,255,.15)}
.line{margin:6px 0}
.who{display:inline-block;min-width:74px;font-weight:bold;font-size:14px;margin-right:8px}
.trans{color:#7D86A0;font-size:13.5px;background:rgba(255,255,255,.03);border-left:3px solid #4A5578;padding:10px 14px;margin:14px 0;border-radius:0 8px 8px 0}
.choice{color:#FFD27A;margin:10px 0 4px}
.opt{color:#C9D0E0;font-size:14px;margin-left:14px}
.end{background:rgba(255,210,122,.06);border:1px solid rgba(255,210,122,.3);border-radius:16px;padding:24px 28px;margin-bottom:28px}
.end h3{color:#FFD27A}
</style></head><body>
<h1>完蛋，我被AI娘包围了</h1>
<div class="sub">完整剧情 v5 · 10 幕 851 行 · 预计 120 分钟 · 每幕附对应 CG · 2026-08-11<br>
<span style="color:#FFD27A">※ 剧中的「陈默」是占位符 —— 游戏内会替换为你设定的名字</span></div>""")

for i, s in enumerate(STORY, 1):
    cg = s["cg"].split("/")[-1]
    b64 = img_b64(cg)
    img_html = f'<img src="{b64}" alt="{cg}">' if b64 else f'<div style="color:#5C6580">CG 缺失：{cg}</div>'
    parts.append(f'<div class="scene"><h2>幕 {i} · {s["title"]}</h2>')
    parts.append(f'<div class="meta">时间：{s["date"]} ｜ CG：{cg}</div>')
    parts.append(img_html)
    for l in s["lines"]:
        if l["t"] == "transition":
            parts.append(f'<div class="trans">◆ 转场（{l.get("date","")}）：{l["text"]}</div>')
        elif l["t"] == "choice":
            parts.append(f'<div class="choice">◇ 选项：{l["text"]}</div>')
            for ch in l["choices"]:
                rp = ch["reply"]
                tag = f" [+{ch.get('affect','')}]" if ch.get("affect") else ""
                parts.append(f'<div class="opt">· {ch["label"]} → {SPK.get(rp["t"],rp["t"])}：{rp["text"]}{tag}</div>')
        else:
            who = SPK.get(l["t"], l["t"])
            color = COLOR.get(l["t"], "#C9D0E0")
            parts.append(f'<div class="line"><span class="who" style="color:{color}">{who}</span>{l["text"]}</div>')
    parts.append("</div>")

parts.append('<h2 style="text-align:center;color:#FFD27A;letter-spacing:.3em">结 局</h2>')
for k, e in ENDINGS.items():
    parts.append(f'<div class="end"><h3>【{k}】{e["title"]}</h3><div>{e["text"]}</div></div>')
parts.append("</body></html>")

html = "\n".join(parts)
outpath = os.path.join(os.path.dirname(cwd), "docs", "story_full_v5.html")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(html)
print("saved:", outpath, len(html) // 1024, "KB")
