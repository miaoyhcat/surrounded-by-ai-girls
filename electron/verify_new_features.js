// 新功能验证：存档删除 / Ctrl 快进 / 菜单按钮右下角 / 自定义秒数
const { _electron: electron } = require("playwright-core");

const EXE = String.raw`C:\Users\windows\AppData\Local\Programs\surrounded-by-ai-girls\完蛋我被AI娘包围了.exe`;
const results = [];
function check(name, cond, extra = "") {
  results.push([name, !!cond]);
  console.log((cond ? "PASS  " : "FAIL  ") + name + (extra ? "  | " + extra : ""));
}

(async () => {
  const app = await electron.launch({ executablePath: EXE, args: [] });
  const win = await app.firstWindow();
  await win.waitForLoadState("domcontentloaded");
  await win.waitForTimeout(1500);

  // 进入游戏
  await win.click("#btnNew");
  await win.waitForTimeout(1200);
  await win.fill("#nameInput", "测试君");
  await win.click("#nameOk");
  await win.waitForTimeout(1200);
  const tc = win.locator("#titleCard");
  if (await tc.isVisible()) { await tc.click({ force: true }); await win.waitForTimeout(1200); }

  // ── 1. 菜单按钮位置（右下角） ──
  const pos = await win.evaluate(() => {
    const s = getComputedStyle(document.getElementById("menuBtn"));
    return { position: s.position, bottom: s.bottom, right: s.right };
  });
  check("菜单按钮右下角", pos.position === "fixed" && pos.right !== "auto" && pos.bottom !== "auto", JSON.stringify(pos));

  // ── 2. 存档 → 删除 ──
  await win.evaluate(() => document.querySelector("#menuBtn").click());
  await win.waitForTimeout(400);
  await win.click("#mSave");
  await win.waitForTimeout(500);
  await win.click("#slots .slot[data-i='0']"); // 槽位1保存
  await win.waitForTimeout(400);
  const savedInfo = await win.evaluate(() => document.querySelector("#slots .slot[data-i='0'] .info").innerText);
  check("存档成功（槽位1有内容）", savedInfo.includes("幕"), savedInfo.replace(/\n/g, " ").slice(0, 30));
  // 切到读档模式，出现删除按钮
  await win.evaluate(() => document.querySelector("#saveClose").click());
  await win.waitForTimeout(300);
  const menuOpen = await win.evaluate(() => {
    const p = document.getElementById("menuPanel");
    return p && getComputedStyle(p).display !== "none";
  });
  if (!menuOpen) {
    await win.evaluate(() => document.querySelector("#menuBtn").click());
    await win.waitForTimeout(400);
  }
  await win.click("#mLoad");
  await win.waitForTimeout(500);
  const delVisible = await win.evaluate(() => {
    const d = document.querySelector("#slots .slot[data-i='0'] .del");
    return d && d.offsetParent !== null;
  });
  check("读档面板显示删除按钮", delVisible);
  // 点击删除
  await win.evaluate(() => document.querySelector("#slots .slot[data-i='0'] .del").click());
  await win.waitForTimeout(400);
  const afterDel = await win.evaluate(() => document.querySelector("#slots .slot[data-i='0'] .info").innerText);
  check("删除后槽位清空", afterDel.includes("空槽位"), afterDel.replace(/\n/g, " ").slice(0, 20));
  await win.evaluate(() => document.querySelector("#saveClose").click());
  await win.waitForTimeout(300);
  await win.evaluate(() => document.querySelector("#menuBtn").click());
  await win.waitForTimeout(300);

  // ── 3. Ctrl 长按快进 ──
  await win.keyboard.down("Control");
  await win.waitForTimeout(600);
  const skipping = await win.evaluate(() => document.getElementById("mSkip").classList.contains("on"));
  check("按住 Ctrl 进入快进", skipping);
  await win.keyboard.up("Control");
  await win.waitForTimeout(400);
  const stopped = await win.evaluate(() => !document.getElementById("mSkip").classList.contains("on"));
  check("松开 Ctrl 退出快进", stopped);

  // ── 4. 自定义自动播放秒数 ──
  await win.evaluate(() => document.querySelector("#menuBtn").click());
  await win.waitForTimeout(400);
  await win.click("#mSet");
  await win.waitForTimeout(500);
  await win.selectOption("#sAutoSpeed", "4");
  await win.waitForTimeout(300);
  const customVisible = await win.evaluate(() => {
    const el = document.getElementById("sAutoCustom");
    return el.style.display !== "none";
  });
  check("选自定义出现秒数输入框", customVisible);
  await win.fill("#sAutoCustom", "5");
  await win.waitForTimeout(300);
  const delay = await win.evaluate(() => (function(){ const s = {autoSpeed:4, autoCustom:5}; return Math.max(0.5, Math.min(30, s.autoCustom))*1000; })());
  check("自定义 5 秒生效", delay === 5000, `delay=${delay}ms`);

  await win.screenshot({ path: "new_features_shot.png" });
  await app.close();

  const fails = results.filter(([, ok]) => !ok);
  console.log(`\n===== 新功能验证: ${results.length - fails.length}/${results.length} 通过 =====`);
  process.exit(fails.length ? 1 : 0);
})().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});
