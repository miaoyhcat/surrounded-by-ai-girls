# -*- coding: utf-8 -*-
"""提取全部场景三个 AI 娘角色的台词 → JSON（供批量配音）"""
import re, json

SRC = r"C:\Users\windows\ZCodeProject\ai-galgame\src\web\demo\data.js"
with open(SRC, encoding="utf-8") as f:
    js = f.read()

scene_starts = [m.start() for m in re.finditer(r'\{\s*id:\s*"s', js)]
scene_ids = re.findall(r'\{\s*id:\s*"([^"]+)"', js)

# 负向后顾排除 choice 行内嵌的 reply:{t:"g",text:"..."}（reply 行无独立配音）
line_re = re.compile(r'(?<!reply:)\{\s*t:\s*"(g|whale|claude|you|narr)",\s*text:\s*"((?:[^"\\]|\\.)*)"')

out = {}
for i, sid in enumerate(scene_ids):
    start = scene_starts[i]
    end = scene_starts[i + 1] if i + 1 < len(scene_starts) else len(js)
    block = js[start:end]
    lines = []
    for m in line_re.finditer(block):
        role, text = m.group(1), m.group(2)
        if role in ("g", "whale", "claude"):
            text = text.replace('\\"', '"').replace("\\n", " ").replace("\\'", "'")
            text = text.replace('\\」', '」').replace('\\「', '「')
            text = text.replace("{PC}", "").replace("陈默", "你").strip()
            lines.append({"role": role, "text": text})
    out[sid] = lines
    cnt = {r: sum(1 for l in lines if l["role"] == r) for r in ("g", "whale", "claude")}
    print(f"{sid}: {len(lines)} 句 (g={cnt['g']} whale={cnt['whale']} claude={cnt['claude']})")

with open(r"D:\tts_scripts\front_scenes.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("总计:", sum(len(v) for v in out.values()), "句 → D:\\tts_scripts\\front_scenes.json")
