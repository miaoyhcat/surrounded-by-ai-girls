# -*- coding: utf-8 -*-
"""TTS-Online 自动化 v2：JS 直接触发点击（绕过弹窗遮挡）"""
import time
from playwright.sync_api import sync_playwright

OUT_DIR = r"D:\tts_samples_online"

JOBS = [
    ("派蒙", "你好呀，人类！我是 GPT！请多指教！虽然我目前只会聊天。", "GPT娘_派蒙"),
    ("三月七", "你好。我是鲸鱼。算你运气好，第一个打开我的人。", "鲸鱼娘_三月七"),
    ("神里绫华", "克劳德。你可以叫我 claude 娘。我不是来投奔的。", "Claude娘_绫华"),
]

def js_click(pg, selector_text):
    """JS 点击包含指定文本的最小元素"""
    return pg.evaluate(f"""() => {{
      const t = '{selector_text}';
      const els = [...document.querySelectorAll('button, div, span, li, label')];
      // 优先精确匹配文本的叶节点
      const el = els.find(e => e.innerText && e.innerText.trim() === t && e.children.length === 0);
      if (el) {{ el.click(); return 'ok:' + el.tagName; }}
      return 'notfound';
    }}""")

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(accept_downloads=True, viewport={"width": 1400, "height": 900})
    pg = ctx.new_page()
    pg.goto("https://acgn.ttson.cn/", timeout=60000)
    pg.wait_for_timeout(3000)

    for role, text, fname in JOBS:
        print(f"\n── {role}：{text[:16]}… ──")
        # 1. 填文本
        pg.fill("textarea.el-textarea__inner", text)
        pg.wait_for_timeout(300)
        # 2. 打开角色选择
        print("  开角色列表:", js_click(pg, "角色选择"))
        pg.wait_for_timeout(1500)
        # 3. 选角色
        print("  选角色:", js_click(pg, role))
        pg.wait_for_timeout(800)
        # 4. JS 点生成
        print("  生成:", js_click(pg, "生成"))
        # 5. 轮询下载（最多 90s）
        ok = False
        for i in range(90):
            pg.wait_for_timeout(1000)
            st = pg.evaluate("() => { const d = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === '下载'); return d ? getComputedStyle(d).pointerEvents : 'none'; }")
            if st == "none" or st is None:
                continue
            try:
                print(f"  下载按钮可用({i+1}s)，触发下载…")
                with pg.expect_download(timeout=60000) as dl_info:
                    js_click(pg, "下载")
                d = dl_info.value
                d.save_as(rf"{OUT_DIR}\{fname}.{d.suggested_filename.split('.')[-1]}")
                print("  ✓", d.suggested_filename)
                ok = True
                break
            except Exception as e:
                print("  下载失败:", str(e)[:80])
        if not ok:
            print("  ✗ 超时")
        pg.fill("textarea.el-textarea__inner", "")

    b.close()
print("\n完成")
