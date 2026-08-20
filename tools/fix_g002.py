# -*- coding: utf-8 -*-
"""修复 s1/g_002：'你好呀，人类！我是 GPT~ 请多指教！——虽然…' 后半句合成截断"""
import os, sys, time
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
sys.path.insert(0, r"D:\index-tts")
os.chdir(r"D:\index-tts")
import torch
from indextts.infer_v2_5 import IndexTTS2

print("加载 IndexTTS-2.5…", flush=True)
t0 = time.time()
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints",
                device="cuda:0" if torch.cuda.is_available() else "cpu", use_bf16=True)
tts.low_vram = False
print(f"模型就绪 {time.time()-t0:.0f}s", flush=True)

# GPT娘 = 卡齐娜 12s 参考音（与正式合成一致）
REF = r"D:\tts_dry\kachiina_ref12s.wav"
TEXT = "你好呀，人类！我是 GPT~ 请多指教！——虽然我目前只会聊天。会一点中文，会一点英文，会一点「看起来听懂了」。"
OUT = r"D:\tts_voice\s1\g_002.wav"

if torch.cuda.is_available():
    torch.cuda.empty_cache()
for attempt in range(3):
    try:
        tts.infer(spk_audio_prompt=REF, text=TEXT, output_path=OUT,
                  lang="zh", use_random=False, verbose=False)
        print(f"✓ 合成完成 → {OUT}", flush=True)
        break
    except Exception as e:
        print(f"⚠ 第{attempt+1}次失败: {str(e)[:120]}", flush=True)
        if attempt == 2:
            sys.exit(1)
        time.sleep(3)
