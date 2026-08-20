# -*- coding: utf-8 -*-
"""提取游戏三个角色的台词 → 整理成配音脚本"""
import re, os

SRC = r"C:\Users\windows\ZCodeProject\ai-galgame\src\web\demo\data.js"
OUT_DIR = r"D:\tts_scripts"
os.makedirs(OUT_DIR, exist_ok=True)

with open(SRC, encoding="utf-8") as f:
    js = f.read()

lines = re.findall(r'\{t:"(g|whale|claude|you|narr)",\s*text:"((?:[^"\\]|\\.)*)"\}', js)
roles = {"g": "GPT娘", "whale": "鲸鱼娘", "claude": "Claude娘"}
out = {r: [] for r in roles}
for t, text in lines:
    if t in roles:
        text = text.replace("\\\"", '"').replace("\\n", " ").replace("\\'", "'")
        text = text.replace("{PC}", "（电脑配置）").replace("陈默", "你")
        out[t].append(text.strip())

with open(os.path.join(OUT_DIR, "角色台词.txt"), "w", encoding="utf-8") as f:
    for r, name in roles.items():
        f.write(f"===== {name}（{len(out[r])} 句）=====\n")
        for i, t in enumerate(out[r], 1):
            f.write(f"{i}. {t}\n")
        f.write("\n")

print("GPT娘:", len(out["g"]), "句")
print("鲸鱼娘:", len(out["whale"]), "句")
print("Claude娘:", len(out["claude"]), "句")
print("输出:", os.path.join(OUT_DIR, "角色台词.txt"))
