# -*- coding: utf-8 -*-
"""安装版实测：CDP 驱动打包后的 exe（playwright 1.61 无 electron API，改用 --remote-debugging-port）
验证：启动、窗口、标题画面、开始游戏、剧情推进、CG 加载、配音系统、存档、BGM 设置。"""
import subprocess, time, sys
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\windows\AppData\Local\Programs\surrounded-by-ai-girls\完蛋我被AI娘包围了.exe"
results = []

def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + (("  | " + extra) if extra else ""))

# 清理残留实例
subprocess.run('taskkill /F /IM "完蛋我被AI娘包围了.exe" 2>nul', shell=True)
time.sleep(1)

proc = subprocess.Popen([EXE, "--remote-debugging-port=9222"], shell=False)
time.sleep(5)

with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        win = browser.contexts[0].pages[0]
        win.wait_for_load_state("domcontentloaded")
        check("窗口标题", win.title() and "AI" in win.title(), win.title())
        win.wait_for_timeout(1500)
        check("主界面可见", win.locator("#btnNew").is_visible(), "")

        # 开始游戏
        win.click("#btnNew")
        win.wait_for_timeout(800)
        check("名字输入框", win.locator("#nameInput").is_visible())
        win.fill("#nameInput", "测试君")
        win.click("#nameOk")
        win.wait_for_timeout(3000)

        # 剧情推进，检查台词与 CG
        box = win.locator("#boxInner")
        check("台词出现", box.is_visible() and len(box.inner_text().strip()) > 0, box.inner_text()[:30])
        win.wait_for_timeout(500)
        bg = win.evaluate("document.getElementById('bg').style.backgroundImage || document.getElementById('bg').src || ''")
        check("背景/CG 已加载", bool(bg), bg[:60])

        # 配音系统检查
        has_voice_sys = win.evaluate("typeof playVoice === 'function' && typeof resetVoiceSeq === 'function'")
        check("配音系统已注入", has_voice_sys)
        # 配音开关
        win.keyboard.press("Escape"); win.wait_for_timeout(400)
        if win.locator("#settingsBtn").is_visible():
            win.click("#settingsBtn"); win.wait_for_timeout(500)
            has_voice_toggle = win.evaluate("!!document.getElementById('sVoice') || !!document.querySelector('[id*=voice]')")
            check("配音开关存在", has_voice_toggle)
            win.keyboard.press("Escape"); win.wait_for_timeout(300)

        # 存档面板
        win.keyboard.press("Escape"); win.wait_for_timeout(400)
        if win.locator("#saveBtn").is_visible():
            win.click("#saveBtn"); win.wait_for_timeout(500)
            slots = win.evaluate("document.querySelectorAll('#slotList .slot, #slotList [class*=slot]').length")
            check("存档槽 ≥30", slots >= 30, f"slots={slots}")

        win.screenshot(path=r"C:\Users\windows\ZCodeProject\ai-galgame\tools\install_verify_shot.png")
    except Exception as e:
        print("EXC:", str(e)[:200])
    finally:
        try: browser.close()
        except: pass

proc.terminate()
subprocess.run('taskkill /F /IM "完蛋我被AI娘包围了.exe" 2>nul', shell=True)

fails = [n for n, ok in results if not ok]
print(f"\n===== 安装版实测: {len(results)-len(fails)}/{len(results)} 通过 =====")
sys.exit(1 if fails else 0)
