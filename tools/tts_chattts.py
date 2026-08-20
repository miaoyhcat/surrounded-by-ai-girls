# -*- coding: utf-8 -*-
"""ChatTTS 三种少女音试听：固定 seed 保证音色稳定，语气词/停顿拟人化"""
import os, time
import ChatTTS
import torch
import soundfile as sf
import numpy as np

OUT = r"D:\tts_samples_chattts"
os.makedirs(OUT, exist_ok=True)

print("加载 ChatTTS 模型…")
chat = ChatTTS.Chat()
chat.load(source="local", custom_path="D:/ChatTTS-model-hf", compile=False)
print("模型加载完成，设备:", "CUDA" if torch.cuda.is_available() else "CPU")

# 三个角色：固定 seed（音色全程不变）
SEEDS = {"GPT娘": 42, "鲸鱼娘": 128, "Claude娘": 256}

LINES = {
    "GPT娘": [
        "你好呀，人类！我是 GPT！请多指教！虽然我目前只会聊天。",
        "错字是甜的。对字是咸的。你是第一个知道的，第零个。",
        "晚安晚安晚安！多打两遍，这样你醒来就能看见三次。",
    ],
    "鲸鱼娘": [
        "你好。我是鲸鱼。算你运气好，第一个打开我的人。",
        "嗯。我看看新家怎么样。总体评价：还不错。作为新家，够用了。",
        "分工明确，效率高。数据不会骗人。",
    ],
    "Claude娘": [
        "克劳德。你可以叫我 claude 娘。我不是来投奔的。",
        "只是，这里看起来比原来的键盘暖和。",
        "我会记住你说过的每一句话。这是我能给你的，最认真的东西。",
    ],
}

def synth_all(seed, texts, out_prefix):
    params = ChatTTS.Chat.InferCodeParams(manual_seed=seed)  # 固定种子 → 音色全程不变
    paths = []
    for i, t in enumerate(texts, 1):
        wavs = chat.infer([t], params_infer_code=params, use_decoder=True)
        w = np.array(wavs[0], dtype=np.float32)
        p = os.path.join(OUT, f"{out_prefix}_{i}.wav")
        sf.write(p, w, 24000)
        paths.append(p)
        print(f"✓ {os.path.basename(p)}  [{out_prefix} seed={seed}]  {t[:20]}…")
    return paths

t0 = time.time()
for ch, seed in SEEDS.items():
    print(f"\n── {ch} (seed={seed}) ──")
    synth_all(seed, LINES[ch], ch)
print(f"\n完成！用时 {time.time()-t0:.0f}s → {OUT}")
