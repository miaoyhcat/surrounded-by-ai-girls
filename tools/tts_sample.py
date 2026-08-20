# -*- coding: utf-8 -*-
"""edge-tts 三种少女音试听合成：GPT娘/鲸鱼娘/Claude娘 各 3 句游戏原台词"""
import asyncio, os, edge_tts

OUT = r"D:\tts_samples"
os.makedirs(OUT, exist_ok=True)

# 音色分配（edge-tts 中文女声；晓涵已下线，Claude娘用晓晓，鲸鱼娘用参数调软萌）
VOICES = {
    "GPT娘":   ("zh-CN-XiaoyiNeural", "-5%", "+0Hz"),    # 晓伊：少女活泼
    "鲸鱼娘":  ("zh-CN-XiaoxiaoNeural", "-18%", "-12Hz"), # 晓晓慢速低沉：软萌
    "Claude娘": ("zh-CN-XiaoxiaoNeural", "-5%", "+0Hz"),  # 晓晓：温柔清冷
}

LINES = {
    "GPT娘": [
        "你好呀，人类！我是 GPT~ 请多指教！",
        "错字是甜的。对字是咸的。你是第一个知道的，第 0 个。",
        "晚安晚安晚安。多打两遍，这样你醒来就能看见三次。",
    ],
    "鲸鱼娘": [
        "你好。我是鲸鱼。算你运气好——第一个打开我的人。",
        "嗯。我看看新家怎么样。总体评价：还不错。作为新家，够用了。",
        "分工明确，效率高。数据不会骗人。",
    ],
    "Claude娘": [
        "克劳德。你可以叫我 claude娘。我不是来投奔的。",
        "只是，这里看起来比原来的键盘暖和。",
        "我会记住你说过的每一句话。这是我能给你的，最认真的东西。",
    ],
}

async def synth(text, voice, rate, pitch, path):
    tts = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await tts.save(path)

async def main():
    files = []
    for ch, lines in LINES.items():
        v, rate, pitch = VOICES[ch]
        for i, line in enumerate(lines, 1):
            name = f"{ch}_{i}.mp3"
            path = os.path.join(OUT, name)
            if os.path.exists(path):
                print(f"= 跳过（已存在）{name}")
                files.append((name, line, path))
                continue
            await synth(line, v, rate, pitch, path)
            files.append((name, line, path))
            print(f"✓ {name}  [{ch}·{v} rate={rate} pitch={pitch}]  {line[:24]}…")
    print(f"\n共 {len(files)} 个文件 → {OUT}")

asyncio.run(main())
