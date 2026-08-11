# -*- coding: utf-8 -*-
"""《完蛋，我被AI娘包围了》角色配音生成脚本（ChatTTS 本地）
- 解析 data.js，为 g（GPT娘）/ whale（鲸鱼娘）台词按出现顺序生成 mp3
- 固定音色种子：gpt娘=42，鲸鱼娘=888（seed 决定随机 speaker）
- 输出：src/web/demo/voice/g_N.mp3 / whale_N.mp3
用法：python tools/gen_voice.py [--start N] [--only g|whale]
"""
import os, re, sys, time, wave, subprocess, argparse

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS = os.path.join(BASE, "src", "web", "demo", "data.js")
OUT_DIR = os.path.join(BASE, "src", "web", "demo", "voice")
os.makedirs(OUT_DIR, exist_ok=True)

SEEDS = {"g": 42, "whale": 888}

def extract_lines():
    """用正则提取所有 {t:"g"/"whale", text:"..."} 台词（与 game.html 编号顺序一致）"""
    with open(DATA_JS, "r", encoding="utf-8") as f:
        src = f.read()
    lines = []
    for m in re.finditer(r'\{t:"(g|whale)",\s*text:"((?:[^"\\]|\\.)*)"\}', src):
        t, text = m.group(1), m.group(2)
        text = text.replace('\\"', '"').replace("\\」", "」").replace("\\「", "「")
        lines.append((t, text))
    return lines

def clean(text):
    """清洗舞台指示与符号，只留要读出来的台词"""
    text = re.sub(r'[（(][^（()）]*[)）]', '', text)      # (小声)（纸条）等舞台指示
    text = text.replace('\\"', '"').replace('「', '').replace('」', '')
    text = text.replace('"', '').replace("'", '').replace('~', '。')
    text = text.replace('——', '——')  # 保留破折号停顿
    text = re.sub(r'\s+', '', text)
    text = text.replace('……', '……')  # 保留省略号停顿
    return text.strip()

def split_long(text, limit=70):
    """长句按标点拆段，保证每段 ≤ limit 字"""
    if len(text) <= limit:
        return [text] if text else []
    parts = re.split(r'(?<=[。！？])', text)
    out, buf = [], ""
    for p in parts:
        if len(buf) + len(p) > limit and buf:
            out.append(buf); buf = p
        else:
            buf += p
    if buf: out.append(buf)
    return [s for s in out if s.strip()]

def save_wav(data, path):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000)
        wf.writeframes(data.astype("<i2").tobytes())

def wav_to_mp3(wav_path, mp3_path):
    subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", wav_path, "-codec:a", "libmp3lame",
                    "-b:a", "128k", mp3_path], check=True)
    os.remove(wav_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0, help="从第 N 条开始（断点续跑）")
    ap.add_argument("--only", choices=["g", "whale"], default=None)
    ap.add_argument("--count", type=int, default=99999)
    args = ap.parse_args()

    import numpy as np
    import ChatTTS
    import random

    chat = ChatTTS.Chat()
    if not chat.load(compile=False, source="huggingface"):
        print("!! 模型加载失败"); sys.exit(1)
    import torch
    print("CUDA:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")

    lines = extract_lines()
    print(f"共 {len(lines)} 条台词")

    stats = {"g": 0, "whale": 0}
    t0 = time.time()
    done = 0
    for idx, (t, text) in enumerate(lines):
        if idx < args.start: continue
        if args.only and t != args.only: continue
        if done >= args.count: break
        stats[t] += 1
        num = stats[t]
        fname = f"{t}_{num}.mp3"
        fpath = os.path.join(OUT_DIR, fname)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            continue  # 已生成
        cleaned = clean(text)
        if not cleaned:
            print(f"[{idx}] {fname} EMPTY, 原文: {text[:40]}"); continue
        # 固定音色种子
        random.seed(SEEDS[t])
        spk = chat.sample_random_speaker()
        params = ChatTTS.Chat.InferCodeParams(
            spk_emb=spk, temperature=0.3, top_P=0.7, top_K=20,
            prompt="[speed_5]" if t == "g" else "[speed_4]",
        )
        try:
            segs = split_long(cleaned)
            wavs = []
            for seg in segs:
                out = chat.infer([seg], use_decoder=True, params_infer_code=params)
                wavs.append(out[0].astype(np.float32))
            wav = np.concatenate(wavs) if len(wavs) > 1 else wavs[0]
            tmp = os.path.join(OUT_DIR, fname.replace(".mp3", ".wav"))
            save_wav(wav, tmp)
            wav_to_mp3(tmp, fpath)
            dur = len(wav) / 24000
            done += 1
            if done % 10 == 0 or idx == len(lines) - 1:
                el = time.time() - t0
                print(f"[{idx}] {fname} {dur:.1f}s 用时{el:.0f}s 累计{done}条")
        except Exception as e:
            print(f"[{idx}] {fname} FAIL: {str(e)[:80]} | {cleaned[:30]}")
    print(f"完成：{done} 条新生成，总耗时 {(time.time()-t0)/60:.1f} 分钟")

if __name__ == "__main__":
    main()
