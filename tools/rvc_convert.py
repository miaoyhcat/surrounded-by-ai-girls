# -*- coding: utf-8 -*-
"""Applio RVC 变声：男声干声 → 三种少女音色"""
import os, sys
os.chdir(r"D:\Applio")
sys.path.insert(0, r"D:\Applio")

from rvc.infer.infer import VoiceConverter

W = r"D:\Applio\assets\weights"
OUT = r"D:\tts_rvc"
os.makedirs(OUT, exist_ok=True)

# 三个少女模型 + 对应干声
JOBS = [
    ("初音Miku", os.path.join(W, "Miku", "model.pth"),
     os.path.join(W, "Miku", "model.index"), r"D:\tts_dry\dry_1.wav", "Miku_1.wav"),
    ("芭芭拉", os.path.join(W, "Barbara", "barbara-jp.pth"),
     os.path.join(W, "Barbara", "added_IVF4361_Flat_nprobe_1_barbara-jp_v2.index"), r"D:\tts_dry\dry_2.wav", "Barbara_1.wav"),
    ("派蒙", os.path.join(W, "Paimon", "paimon-jp.pth"),
     os.path.join(W, "Paimon", "added_IVF3904_Flat_nprobe_1_paimon-jp_v2.index"), r"D:\tts_dry\dry_3.wav", "Paimon_1.wav"),
]

vc = VoiceConverter()
for name, model, index, src, out in JOBS:
    print(f"\n── {name} ──")
    try:
        vc.convert_audio(
            audio_input_path=src,
            audio_output_path=os.path.join(OUT, out),
            model_path=model,
            index_path=index,
            pitch=0,
            f0_method="rmvpe",
            index_rate=0.75,
            embedder_model="contentvec",
            export_format="WAV",
        )
        print(f"✓ {out} 完成")
    except Exception as e:
        print(f"✗ {name} 失败: {str(e)[:200]}")
print("\n全部完成 →", OUT)
