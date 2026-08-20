// 安装版实测：playwright-core 的 _electron 直接驱动打包后的 exe
// 验证：启动、窗口、标题画面、开始游戏、剧情推进、CG 加载、存档槽、BGM 设置、相册
const { _electron: electron } = require("playwright-core");
const path = require("path");

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
  await win.waitForTimeout(1800);

  const title = await win.title();
  check("窗口标题", title.includes("AI") || title.length > 0, title);
  check("主界面可见", await win.locator("#btnNew").isVisible());

  // 开始游戏
  await win.click("#btnNew");
  await win.waitForTimeout(1200);
  check("名字输入框", await win.locator("#nameInput").isVisible());
  await win.fill("#nameInput", "测试君");
  await win.click("#nameOk");
  await win.waitForTimeout(1200);
  // 点掉标题卡（点击开始 ▸）进入剧情
  const tc = win.locator("#titleCard");
  if (await tc.isVisible()) {
    await tc.click({ force: true });
    await win.waitForTimeout(1500);
  }
  check("标题卡已进入剧情", !(await tc.isVisible()));

  // 剧情台词 + 背景 CG
  const box = win.locator("#boxInner");
  const txt = await box.innerText();
  check("台词出现", txt.trim().length > 0, txt.trim().slice(0, 30));
  const bgInfo = await win.evaluate(() => {
    const el = document.getElementById("cg");
    if (!el) return "NO #cg";
    return el.style.backgroundImage || "";
  });
  check("背景/CG 已加载", bgInfo.includes("url("), String(bgInfo).slice(0, 60));
  // 本作是全屏 CG 模式（无角色立绘元素），确认画面为 CG 全覆盖
  const fullBg = await win.evaluate(() => {
    const cg = document.getElementById("cg");
    if (!cg) return false;
    const r = cg.getBoundingClientRect();
    return r.width >= window.innerWidth * 0.99 && r.height >= window.innerHeight * 0.99;
  });
  check("CG 全屏显示", fullBg);

  // 推进剧情
  await win.click("#boxInner");
  await win.waitForTimeout(400);
  const txt2 = await box.innerText();
  check("剧情可推进", txt2.trim().length > 0, txt2.trim().slice(0, 30));

  // 菜单 → 存档面板（与 e2e 相同操作序列）
  await win.evaluate(() => document.querySelector("#menuBtn").click());
  await win.waitForTimeout(400);
  const saveBtn = win.locator("#mSave");
  check("菜单-存档按钮可见", await saveBtn.isVisible());
  if (await saveBtn.isVisible()) await saveBtn.click();
  await win.waitForTimeout(600);
  const slots = await win.evaluate(
    () => document.querySelectorAll("#slots .slot").length
  );
  check("存档槽 ≥30", slots >= 30, `slots=${slots}`);

  // 设置 → BGM
  await win.evaluate(() => document.querySelector("#saveClose").click());
  await win.waitForTimeout(300);
  // 菜单可能仍开着（savePanel 浮在菜单上），确保菜单打开再点设置
  const menuVisible = await win.evaluate(() => {
    const p = document.getElementById("menuPanel");
    return p && getComputedStyle(p).display !== "none";
  });
  if (!menuVisible) {
    await win.evaluate(() => document.querySelector("#menuBtn").click());
    await win.waitForTimeout(400);
  }
  const setBtn = win.locator("#mSet");
  check("菜单-设置按钮可见", await setBtn.isVisible());
  if (await setBtn.isVisible()) await setBtn.click();
  await win.waitForTimeout(500);
  const hasBgm = await win.evaluate(() => {
    const el = document.getElementById("sBgm");
    return !!el;
  });
  check("BGM 设置项存在", hasBgm);

  // 相册
  await win.evaluate(() => localStorage.setItem("aigirls_cg_unlocked", '{"s1":1}'));
  await win.evaluate(() => (location.href = "index.html"));
  await win.waitForTimeout(1800);
  const albumBtn = win.locator("#btnAlbum");
  if (await albumBtn.isVisible()) await albumBtn.click();
  await win.waitForTimeout(700);
  const gridVisible = await win.locator("#albumGrid").isVisible();
  check("回忆相册打开", gridVisible);
  const cards = await win.evaluate(() => document.querySelectorAll("#albumGrid .card").length);
  check("相册有卡片", cards > 0, `cards=${cards}`);

  await win.screenshot({ path: path.join(__dirname, "install_verify_shot.png") });
  await app.close();

  const fails = results.filter(([, ok]) => !ok);
  console.log(`\n===== 安装版实测: ${results.length - fails.length}/${results.length} 通过 =====`);
  process.exit(fails.length ? 1 : 0);
})().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});
