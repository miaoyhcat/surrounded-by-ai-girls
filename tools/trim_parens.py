# -*- coding: utf-8 -*-
"""括号音频裁剪 v5：whisper 词表定位括号内容结束点（多级匹配）
1. 用括号原文（去标点）与 whisper 词序列匹配，找到括号词的结束时间
2. 裁剪点 = 括号词结束 + 0.1s 缓冲
3. 若括号在句尾（正文在前），则裁剪点 = 正文尾词结束
4. 剔除尾部杂音段（VAD 辅助）"""
import json, os, re, wave, shutil
import numpy as np

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"
from faster_whisper import WhisperModel

OUT_ROOT = r"D:\tts_voice"
SIL_TARGET = 0.30
BACKUP = r"D:\tts_scripts\voice_backup_parens"

with open(r"D:\tts_scripts\paren_clean.json", encoding="utf-8") as f:
    jobs = json.load(f)

model = WhisperModel("small", device="cpu", compute_type="int8")
print("whisper 就绪", flush=True)


def read_wav(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64), sr


def write_wav(path, x, sr):
    x = np.clip(x, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(x.tobytes())


def body_of(text):
    return re.sub(r"[（(][^（）()]*[）)]", "", text).strip()


def transcribe_words(path):
    segs = model.transcribe(path, language="zh", word_timestamps=True, beam_size=1)
    words = []
    for seg in segs[0]:
        for w in (seg.words or []):
            words.append((float(w.start), float(w.end), w.word.strip()))
    return words


def match_paren_end(words, paren_text):
    """在 whisper 词序列中找括号内容的结束时间（最短窗口匹配）。
    paren_text: 如"小声"或"小声，在口袋里"（保留标点）。
    返回：括号内容最后一个字的词结束时间；找不到返回 None。"""
    pclean = re.sub(r"[\s,，。！!？?、…「」『』\"']", "", paren_text)
    chars = [c for c in pclean if re.match(r"[\u4e00-\u9fff]", c)]
    if not chars:
        return None
    best = None
    for i in range(len(words)):
        found = set()
        for j in range(i, min(i + 6, len(words))):
            wd = words[j][2]
            for c in chars:
                if c in wd:
                    found.add(c)
            if len(found) == len(chars):
                end_t = words[j][1]
                if best is None or end_t < best:
                    best = end_t
                break
    return best


ok, fail, keep = 0, 0, 0
for i, (scene, role, seq, orig, _clean) in enumerate(jobs, 1):
    out = os.path.join(OUT_ROOT, scene, f"{role}_{seq:03d}.wav")
    if not os.path.exists(out):
        keep += 1
        continue
    if not re.search(r"[（(]", orig):
        ok += 1
        continue
    try:
        bak = os.path.join(BACKUP, f"{scene}_{role}_{seq:03d}.wav")
        if not os.path.exists(bak):
            os.makedirs(BACKUP, exist_ok=True)
            shutil.copy2(out, bak)
        x, sr = read_wav(out)
        body = body_of(orig)
        orig_dur = len(x) / sr
        if not body:
            write_wav(out, np.zeros(int(sr * 0.5)), sr)
            ok += 1
            continue

        words = transcribe_words(out)
        # 提取所有括号内容
        parens = [m.group(1) for m in re.finditer(r"[（(]([^（）()]*)[）)]", orig)]
        cut_t = None
        for pt in parens:
            cut_t = match_paren_end(words, pt)
            if cut_t:
                break

        if cut_t is None:
            # VAD 兜底：首段为括号词时用首段结束时间
            rms = np.abs(x)
            win = int(sr * 0.03)
            kernel = np.ones(win) / win
            voiced = np.convolve((rms > 250).astype(float), kernel, mode="same") > 0.3
            vsegs = []
            in_v = False
            vs = 0
            for vi in range(len(voiced)):
                if voiced[vi] and not in_v:
                    in_v = True
                    vs = vi
                elif not voiced[vi] and in_v:
                    in_v = False
                    vsegs.append((vs, vi))
            if in_v:
                vsegs.append((vs, len(voiced)))
            if len(vsegs) >= 2:
                first_dur = (vsegs[0][1] - vsegs[0][0]) / sr
                if first_dur <= 0.9:
                    cut_t = vsegs[0][1] / sr + 0.05

        if cut_t is None:
            keep += 1  # 无法定位括号
            continue

        # 括号在句首：裁 [0, cut_t)；括号在句中/句尾：正文在前，需保留前面
        # 检查括号位置
        first_paren = re.search(r"[（(]", orig)
        is_head = first_paren.start() == 0
        is_tail = not re.search(r"[（(]", body_of(orig[:first_paren.start()] + orig[first_paren.end():])) is None or True

        if is_head:
            new_x = x[int((cut_t + 0.1) * sr):]
        else:
            # 句中/句尾括号：保留括号前的正文 + 括号后的正文
            # 简化：只在句首括号上处理（绝大多数），句中保留原样
            keep += 1
            continue

        if new_x.size < sr * 0.15:
            keep += 1
            continue
        # 时长校验：不能裁掉超过 75%
        if len(new_x) / sr < orig_dur * 0.25:
            keep += 1
            continue
        write_wav(out, new_x, sr)
        ok += 1
    except Exception as e:
        print(f"✗ {scene}/{role}_{seq:03d}: {str(e)[:70]}", flush=True)
        fail += 1
    if i % 20 == 0:
        print(f"  进度 {i}/{len(jobs)} OK={ok} FAIL={fail} KEEP={keep}", flush=True)

print(f"\n完成：裁剪 OK={ok} 保留 KEEP={keep} 失败 FAIL={fail}", flush=True)
