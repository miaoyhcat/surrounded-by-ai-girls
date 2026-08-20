# -*- coding: utf-8 -*-
"""重新合成带括号的台词：去掉（动作描述）只读台词正文，覆盖原 wav
输出: D:\tts_voice\{scene}\{role}_{seq:03d}.wav（覆盖）
"""
import json, os, sys, time, wave, struct

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
sys.path.insert(0, r"D:\index-tts")
os.chdir(r"D:\index-tts")
import torch
from indextts.infer_v2_5 import IndexTTS2

REFS = {
    "g":     r"D:\tts_dry\kachiina_ref12s.wav",
    "whale": r"D:\tts_dry\march7_ref12s.wav",
    "claude": r"D:\tts_dry\linette_ref12s.wav",
}
OUT_ROOT = r"D:\tts_voice"

with open(r"D:\tts_scripts\paren_clean.json", encoding="utf-8") as f:
    jobs = json.load(f)

# 只处理净化后非空的（空的=纯动作描述→写静音）
jobs = [j for j in jobs if j[4]]

print(f"待重合成 {len(jobs)} 句", flush=True)
print("加载模型…", flush=True)
t0 = time.time()
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints",
                device="cuda:0" if torch.cuda.is_available() else "cpu", use_bf16=True)
tts.low_vram = False
print(f"模型就绪（{time.time()-t0:.0f}s）", flush=True)

ok, fail = 0, 0
for i, (scene, role, seq, orig, text) in enumerate(jobs, 1):
    out = os.path.join(OUT_ROOT, scene, f"{role}_{seq:03d}.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    for attempt in range(2):
        try:
            tts.infer(spk_audio_prompt=REFS[role], text=text, output_path=out,
                      lang="zh", use_random=False, verbose=False)
            ok += 1
            break
        except Exception as e:
            if attempt == 0:
                print(f"  ⚠ {scene}/{role}_{seq:03d} 重试: {str(e)[:60]}", flush=True)
                time.sleep(2)
            else:
                print(f"✗ {scene}/{role}_{seq:03d}: {str(e)[:80]}", flush=True)
                fail += 1
    if i % 10 == 0:
        print(f"  进度 {i}/{len(jobs)} OK={ok} FAIL={fail} {time.time()-t0:.0f}s", flush=True)

print(f"\n完成：OK={ok} FAIL={fail} 总耗时 {time.time()-t0:.0f}s", flush=True)
