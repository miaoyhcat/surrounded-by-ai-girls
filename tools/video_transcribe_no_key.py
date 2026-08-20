# -*- coding: utf-8 -*-
"""B站视频下载 + 本地转写（不依赖 DeepSeek API key）"""
import subprocess, sys, os
from pathlib import Path

PY = sys.executable
W = Path(r"D:\tts_scripts\video_tmp")
W.mkdir(parents=True, exist_ok=True)
URL = "https://www.bilibili.com/video/BV1EEivB9EQN"

def sh(cmd, timeout):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout, r.stderr
    except Exception as e:
        return False, "", str(e)

# 1. 下载音频
a = W / "a.mp3"; a.unlink(missing_ok=True)
ok, _, e = sh(["yt-dlp", "-x", "--audio-format", "mp3", "-o", str(a), "--no-playlist", URL], 300)
if not ok or not a.exists():
    print("下载失败:", e[-200:]); sys.exit(1)
print(f"音频 OK: {a.stat().st_size//1024}KB")

# 2. 转写（FunASR → Whisper 兜底）
text = ""
ok, _, _ = sh([PY, "-m", "pip", "show", "funasr"], 5)
if ok:
    ok, out, _ = sh([PY, "-c", f"from funasr import AutoModel; m=AutoModel(model='iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',disable_update=True,disable_progress=True); r=m.generate(input=r'{a.resolve()}'); print(r[0]['text'])"], 600)
    if ok and out.strip():
        text = "".join(l for l in out.strip().split("\n") if not l.startswith(("Download", "Processing", "funasr")) and l.strip()).replace(" ", "")
if not text:
    ok, out, _ = sh([PY, "-c", f"import whisper; m=whisper.load_model('tiny'); r=m.transcribe(r'{a.resolve()}',language='zh',verbose=False); print(r['text'])"], 1800)
    if ok and out.strip():
        text = out.strip()
if not text:
    print("转写失败"); sys.exit(1)

out_p = r"D:\tts_scripts\video_transcript.txt"
with open(out_p, "w", encoding="utf-8") as f:
    f.write(text)
print(f"转写完成: {len(text)} 字 → {out_p}")
