# -*- coding: utf-8 -*-
"""批量合成全部场景配音：三个角色固定音色（声线统一）
输出: D:\tts_voice\{scene}\{role}_{seq:03d}.wav
"""
import json, os, sys, time

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
sys.path.insert(0, r"D:\index-tts")
os.chdir(r"D:\index-tts")
import torch
from indextts.infer_v2_5 import IndexTTS2

# 角色 → 参考音频（声线锁定）
REFS = {
    "g":     r"D:\tts_dry\kachiina_ref12s.wav",  # GPT娘 = 卡齐娜（12s 裁剪版）
    "whale": r"D:\tts_dry\march7_ref12s.wav",    # 鲸鱼娘 = 三月七（12s 裁剪版）
    "claude": r"D:\tts_dry\linette_ref12s.wav",  # Claude娘 = 琳妮特（12s 裁剪版）
}
ROLE_NAMES = {"g": "GPT娘", "whale": "鲸鱼娘", "claude": "Claude娘"}
OUT_ROOT = r"D:\tts_voice"
MAIN_SCENES = ["s1", "s2", "s3", "s4", "s5", "s5b", "s6",
               "s6a", "s6b", "s6c", "s7", "s7w", "s7c", "s7g", "s7a"]  # 全部场景

with open(r"D:\tts_scripts\front_scenes.json", encoding="utf-8") as f:
    data = json.load(f)

jobs = []
for scene in MAIN_SCENES:
    seq = {"g": 0, "whale": 0, "claude": 0}
    for line in data.get(scene, []):
        role = line["role"]
        seq[role] += 1
        jobs.append({
            "scene": scene, "role": role, "seq": seq[role],
            "text": line["text"], "ref": REFS[role],
        })

print(f"待合成 {len(jobs)} 句（GPT娘={sum(1 for j in jobs if j['role']=='g')} 鲸鱼娘={sum(1 for j in jobs if j['role']=='whale')} Claude娘={sum(1 for j in jobs if j['role']=='claude')}）", flush=True)

# 每 N 句重启进程（防 GPU 推理速度退化）：由外层循环传入，处理完即退出
MAX_JOBS_PER_RUN = int(os.environ.get("TTS_MAX_JOBS", "0"))  # 0 = 不限制

print("加载模型…", flush=True)
t0 = time.time()
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints",
                device="cuda:0" if torch.cuda.is_available() else "cpu", use_bf16=True)
tts.low_vram = False  # bf16 显存充足，关闭长句拆段（提速）
print(f"模型就绪（{time.time()-t0:.0f}s, device={'CUDA' if torch.cuda.is_available() else 'CPU'}）", flush=True)

# 预加载三个参考音频的说话人嵌入（声线锁定，一次计算）
# IndexTTS 的 infer 每次传 spk_audio_prompt 路径即可（内部会加载裁剪），保持传路径保证一致

ok, fail = 0, 0
run_count = 0
for i, job in enumerate(jobs, 1):
    if MAX_JOBS_PER_RUN and run_count >= MAX_JOBS_PER_RUN:
        print(f"  本进程已达上限 {MAX_JOBS_PER_RUN} 句，退出（外层循环会重启）", flush=True)
        break
    out_dir = os.path.join(OUT_ROOT, job["scene"])
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{job['role']}_{job['seq']:03d}.wav")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        ok += 1
        continue
    # 每句前清显存缓存（防碎片累积导致速度退化）
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    for attempt in range(2):  # 偶发 DLL 加载失败自动重试一次
        try:
            tts.infer(spk_audio_prompt=job["ref"], text=job["text"], output_path=out,
                      lang="zh", use_random=False, verbose=False)
            ok += 1
            run_count += 1
            break
        except Exception as e:
            if attempt == 0:
                print(f"  ⚠ [{job['scene']}] {job['role']}_{job['seq']:03d} 重试: {str(e)[:60]}", flush=True)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                time.sleep(2)
            else:
                print(f"✗ [{job['scene']}] {job['role']}_{job['seq']:03d}: {str(e)[:80]}", flush=True)
                fail += 1
    if i % 20 == 0:
        print(f"  进度 {i}/{len(jobs)}（OK={ok} FAIL={fail}）{time.time()-t0:.0f}s", flush=True)

print(f"\n完成：OK={ok} FAIL={fail} 总耗时 {time.time()-t0:.0f}s → {OUT_ROOT}")
print(f"缺失 {fail} 句（可重跑脚本自动补）")
