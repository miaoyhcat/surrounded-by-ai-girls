# -*- coding: utf-8 -*-
"""ChatTTS 三少女音 v3：大采样 + 少女感双指标筛选
- f0 中位数（>220Hz 才算少女音域）
- 频谱质心（清亮度，高=年轻清亮，低=闷沉老气）
选 top 候选 → 3 个角色固定音色合成
"""
import os
import numpy as np
import ChatTTS
import librosa
import soundfile as sf

OUT = r"D:\tts_samples_chattts_v3"
os.makedirs(OUT, exist_ok=True)

TEST = "今天天气真好呀，我们去散步吧！"
N_SAMPLE = 100
F0_MIN = 215.0  # 少女音域下限

print("加载模型…")
chat = ChatTTS.Chat()
chat.load(source="local", custom_path="D:/ChatTTS-model-hf", compile=False)

def synth_one(text, spk_emb, seed=42):
    params = ChatTTS.Chat.InferCodeParams(spk_emb=spk_emb, manual_seed=seed)
    wavs = chat.infer([text], params_infer_code=params, use_decoder=True)
    return np.array(wavs[0], dtype=np.float32)

def analyze(wav):
    f0, _, _ = librosa.pyin(wav, fmin=60, fmax=600, sr=24000)
    f0m = float(np.nanmedian(f0)) if np.any(~np.isnan(f0)) else 0.0
    cent = float(np.mean(librosa.feature.spectral_centroid(y=wav, sr=24000)))
    return f0m, cent

# ── 1. 大采样 + 分析 ──
print(f"采样 {N_SAMPLE} 个音色并分析…")
cands = []
for i in range(N_SAMPLE):
    spk = chat.sample_random_speaker()
    try:
        wav = synth_one(TEST, spk)
        f0m, cent = analyze(wav)
        cands.append((f0m, cent, spk))
    except Exception:
        pass
    if (i + 1) % 20 == 0:
        print(f"  {i+1}/{N_SAMPLE}")

# ── 2. 少女感评分：f0 达标 + 清亮度 ──
girls = [c for c in cands if c[0] >= F0_MIN]
girls.sort(key=lambda c: (c[1], c[0]), reverse=True)  # 清亮度优先
print(f"\n采样完成：{len(cands)} 有效，少女音域(f0≥{F0_MIN}) {len(girls)} 个")
print("top 8 候选（f0 / 清亮度）:")
for i, (f, cen, _) in enumerate(girls[:8]):
    print(f"  #{i+1}  f0={f:.0f}Hz  清亮度={cen:.0f}")

# ── 3. 均匀挑 3 个 ──
n = len(girls)
if n < 3:
    print("!! 少女音不足，放宽阈值到 200Hz")
    girls = sorted([c for c in cands if c[0] >= 200.0], key=lambda c: (c[1], c[0]), reverse=True)
    n = len(girls)
idx = [0, n // 2, n - 1] if n >= 3 else list(range(n))
chosen = [girls[i] for i in idx[:3]]
ROLES = ["GPT娘", "鲸鱼娘", "Claude娘"]

print("\n── 选定 3 个音色 ──")
for r, (f, cen, _) in zip(ROLES, chosen):
    print(f"  {r}: f0={f:.0f}Hz  清亮度={cen:.0f}")

# ── 4. 正式合成（各自固定音色向量）──
LINES = {
    "GPT娘": [
        "你好呀，人类！我是 GPT！请多指教！",
        "错字是甜的。对字是咸的。你是第一个知道的。",
        "晚安晚安晚安！多打两遍，你醒来就能看见三次。",
    ],
    "鲸鱼娘": [
        "你好。我是鲸鱼。算你运气好，第一个打开我的人。",
        "嗯。我看看新家怎么样。总体评价：还不错。",
        "分工明确，效率高。数据不会骗人。",
    ],
    "Claude娘": [
        "克劳德。你可以叫我 claude 娘。我不是来投奔的。",
        "只是，这里看起来比原来的键盘暖和。",
        "我会记住你说过的每一句话。",
    ],
}
for role, (f0, cen, spk) in zip(ROLES, chosen):
    for i, line in enumerate(LINES[role], 1):
        wav = synth_one(line, spk)
        sf.write(os.path.join(OUT, f"{role}_{i}.wav"), wav, 24000)
    print(f"✓ {role} 3 句完成")

print(f"\n完成 → {OUT}")
