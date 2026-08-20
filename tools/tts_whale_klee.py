# -*- coding: utf-8 -*-
"""鲸鱼娘全量重合成：可莉音色（保留括号原文，只换音色）
输出: D:\tts_voice\{scene}\whale_{seq:03d}.wav（覆盖旧三月七版本）
"""
import json, os, sys, time

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
sys.path.insert(0, r"D:\index-tts")
os.chdir(r"D:\index-tts")
import torch
from indextts.infer_v2_5 import IndexTTS2

REF = r"D:\tts_dry\klee_ref12s.wav"  # 鲸鱼娘 = 可莉（新音色）
OUT_ROOT = r"D:\tts_voice"

with open(r"D:\tts_scripts\front_scenes.json", encoding="utf-8") as f:
    data = json.load(f)

# 只取 whale 角色，文本保持原文（含括号）
jobs = []
for scene, lines in data.items():
    seq = 0
    for line in lines:
        if line["role"] == "whale":
            seq += 1
            jobs.append({"scene": scene, "seq": seq, "text": line["text"]})

print(f"待合成 {len(jobs)} 句 whale（可莉音色，原文含括号）", flush=True)
t0 = time.time()
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints",
                device="cuda:0" if torch.cuda.is_available() else "cpu", use_bf16=True)
tts.low_vram = False
print(f"模型就绪（{time.time()-t0:.0f}s）", flush=True)

ok, fail = 0, 0
for i, job in enumerate(jobs, 1):
    out = os.path.join(OUT_ROOT, job["scene"], f"whale_{job['seq']:03d}.wav")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    for attempt in range(2):
        try:
            tts.infer(spk_audio_prompt=REF, text=job["text"], output_path=out,
                      lang="zh", use_random=False, verbose=False)
            ok += 1
            break
        except Exception as e:
            if attempt == 0:
                print(f"  ⚠ {job['scene']}/whale_{job['seq']:03d} 重试: {str(e)[:60]}", flush=True)
                time.sleep(2)
            else:
                print(f"✗ {job['scene']}/whale_{job['seq']:03d}: {str(e)[:80]}", flush=True)
                fail += 1
    if i % 10 == 0:
        print(f"  进度 {i}/{len(jobs)} OK={ok} FAIL={fail} {time.time()-t0:.0f}s", flush=True)

print(f"\n完成：OK={ok} FAIL={fail} 总耗时 {time.time()-t0:.0f}s", flush=True)
