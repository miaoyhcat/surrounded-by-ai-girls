# -*- coding: utf-8 -*-
"""IndexTTS-2.5 三角色配音：三个参考音色 + 游戏台词"""
import os, sys, time
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # HF 镜像（国内）
sys.path.insert(0, r"D:\index-tts")
os.chdir(r"D:\index-tts")
import torch

from indextts.infer_v2_5 import IndexTTS2

OUT = r"D:\tts_indextts"
os.makedirs(OUT, exist_ok=True)

print("加载 IndexTTS-2.5（CUDA）…", flush=True)
t0 = time.time()
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", device="cuda:0" if torch.cuda.is_available() else "cpu")
print(f"模型加载完成 {time.time()-t0:.0f}s", flush=True)

# 三个角色的参考音色
REFS = {
    "GPT娘":   r"D:\tts_samples_online\GPT娘_派蒙.mp3",      # 派蒙（元气）
    "鲸鱼娘":  r"D:\tts_samples_online\鲸鱼娘_三月七.mp3",   # 三月七（甜妹）
    "Claude娘": r"D:\tts_dry\ref_claude.wav",                # 晓晓（温柔，先合成）
}

# Claude娘 参考：edge-tts 晓晓
import asyncio, edge_tts
async def mkref():
    await edge_tts.Communicate("你好，我是你的AI娘，很高兴认识你。", "zh-CN-XiaoxiaoNeural", rate="-5%").save(r"D:\tts_dry\ref_claude.wav")
asyncio.run(mkref())
print("Claude娘参考音频已生成", flush=True)

LINES = {
    "GPT娘": [
        "你好呀，人类！我是 GPT！请多指教！",
        "错字是甜的。对字是咸的。你是第一个知道的。",
    ],
    "鲸鱼娘": [
        "你好。我是鲸鱼。算你运气好，第一个打开我的人。",
        "嗯。我看看新家怎么样。总体评价：还不错。",
    ],
    "Claude娘": [
        "克劳德。你可以叫我 claude 娘。我不是来投奔的。",
        "只是，这里看起来比原来的键盘暖和。",
    ],
}

for role, ref in REFS.items():
    for i, text in enumerate(LINES[role], 1):
        out = os.path.join(OUT, {"GPT娘":"GPT","鲸鱼娘":"WHALE","Claude娘":"CLAUDE"}[role] + f"_{i}.wav")
        print(f"合成 {role}_{i}: {text[:16]}…", flush=True)
        tts.infer(
            spk_audio_prompt=ref,
            text=text,
            output_path=out,
            lang="zh",
            use_random=False,
            verbose=False,
        )
        print(f"  ✓ {out}", flush=True)

print(f"\n全部完成 → {OUT}（总耗时 {time.time()-t0:.0f}s）")
