# -*- coding: utf-8 -*-
"""ChatTTS 三少女音 v2：
1. 采样 30 个候选音色 → 合成测试句 → 基频 f0 筛选（剔除男声/中性声）
2. 选 3 个区分度大的少女音色，分别固定给 GPT娘/鲸鱼娘/Claude娘
3. 每个角色所有句子用同一个 spk_emb → 音色全程一致
"""
import os
import numpy as np
import ChatTTS
import librosa
import soundfile as sf

OUT = r"D:\tts_samples_chattts_v2"
os.makedirs(OUT, exist_ok=True)

TEST = "你好呀，我是你的 AI 娘，请多指教。"
FEMALE_F0 = 195.0  # 女声判定阈值（Hz）

print("加载模型…")
chat = ChatTTS.Chat()
chat.load(source="local", custom_path="D:/ChatTTS-model-hf", compile=False)

def synth_one(text, spk_emb, seed=7):
    params = ChatTTS.Chat.InferCodeParams(spk_emb=spk_emb, manual_seed=seed)
    wavs = chat.infer([text], params_infer_code=params, use_decoder=True)
    return np.array(wavs[0], dtype=np.float32)

def median_f0(wav):
    f0, _, _ = librosa.pyin(wav, fmin=60, fmax=600, sr=24000)
    return float(np.nanmedian(f0)) if np.any(~np.isnan(f0)) else 0.0

# ── 1. 采样候选音色 + 测基频 ──
print("采样候选音色（30 个）并检测音高…")
cands = []
for i in range(30):
    spk = chat.sample_random_speaker()
    try:
        wav = synth_one(TEST, spk)
        f = median_f0(wav)
        cands.append((f, spk))
        print(f"  候选{i}: f0={f:.0f}Hz {'女' if f >= FEMALE_F0 else '男/中性'}")
    except Exception as e:
        print(f"  候选{i}: 失败 {str(e)[:40]}")

females = sorted([c for c in cands if c[0] >= FEMALE_F0], key=lambda x: x[0])
print(f"\n女声候选 {len(females)} 个（f0 {females[0][0]:.0f}~{females[-1][0]:.0f}Hz）")
if len(females) < 3:
    print("!! 女声不足 3 个，降低阈值到 175Hz 再试")
    females = sorted([c for c in cands if c[0] >= 175.0], key=lambda x: x[0])
    print(f"  放宽后 {len(females)} 个")

# ── 2. 均匀挑 3 个：低、中、高（音色区分度大）──
n = len(females)
idx = [0, n // 2, n - 1] if n >= 3 else list(range(n))
chosen = [females[i] for i in idx]
ROLES = ["GPT娘", "鲸鱼娘", "Claude娘"]
assign = {r: c for r, c in zip(ROLES, chosen)}
for r, (f, _) in assign.items():
    print(f"  → {r}: f0={f:.0f}Hz")

# ── 3. 每个角色固定 spk_emb 合成 3 句 ──
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

print("\n── 正式合成（固定音色向量）──")
info = {}
for role, (f0, spk) in assign.items():
    info[role] = f0
    for i, line in enumerate(LINES[role], 1):
        wav = synth_one(line, spk)
        sf.write(os.path.join(OUT, f"{role}_{i}.wav"), wav, 24000)
        print(f"✓ {role}_{i}.wav")

# 音色一致性验证：同一角色重合成第 1 句，对比 spk 相同（代码保证）+ f0 稳定
print("\n── 音色一致性验证（每角色第1句重合成，f0 应一致）──")
for role, (f0, spk) in assign.items():
    wav = synth_one(LINES[role][0], spk)
    f = median_f0(wav)
    print(f"  {role}: 首次 f0={f0:.0f}Hz / 重合成 f0={f:.0f}Hz → {'✓ 稳定' if abs(f - f0) < 15 else '⚠ 波动'}")

print(f"\n完成 → {OUT}")
