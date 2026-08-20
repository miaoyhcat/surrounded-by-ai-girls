// PC 新构建实测：首句不重复 + 读档不跳句 + 相册滚动
// 驱动桌面解压版 exe
const { _electron: electron } = require("playwright-core");
const path = require("path");

const EXE = String.raw`C:\Users\windows\Desktop\完蛋我被AI娘包围了-免安装zip版\完蛋我被AI娘包围了.exe`;
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

  // 新游戏（清档走全新流程）
  check("主界面可见", await win.locator("#btnNew").isVisible());
  await win.evaluate(() => localStorage.clear());
  await win.waitForTimeout(300);
  await win.click("#btnNew");
  await win.waitForTimeout(1500);
  const ni = win.locator("#nameInput");
  if (await ni.isVisible()) {
    await ni.fill("验证君");
    await win.click("#nameOk");
    await win.waitForTimeout(1500);
  } else {
    console.log("NOTE  名字面板未弹出");
  }
  const tc = win.locator("#titleCard");
  if (await tc.isVisible()) { await tc.click({ force: true }); await win.waitForTimeout(1500); }
  check("标题卡已进入剧情", !(await tc.isVisible()));

  // 记录第一句台词
  const firstLine = (await win.locator("#text").innerText()).trim();
  check("第一句台词非空", firstLine.length > 0, firstLine.slice(0, 20));

  // 推进 3 句
  for (let i = 0; i < 3; i++) { await win.click("#boxInner"); await win.waitForTimeout(350); }
  const curBefore = (await win.locator("#text").innerText()).trim();

  // 打开历史记录，统计第一句出现次数
  await win.evaluate(() => document.querySelector("#menuBtn").click());
  await win.waitForTimeout(400);
  await win.evaluate(() => document.querySelector("#mHist").click());
  await win.waitForTimeout(600);
  const histLines = await win.evaluate(() => {
    const h = document.getElementById("histList");
    return h ? Array.from(h.children).map(e => e.textContent.trim()).filter(t => t.length > 0) : [];
  });
  console.log("  历史行数:", histLines.length, "| 首行:", (histLines[0] || "").slice(0, 16));
  const firstCount = histLines.filter(t => t.includes(firstLine.slice(0, 8))).length;
  check("首句只出现 1 次（历史）", firstCount === 1, `count=${firstCount}`);
  check("历史无连续重复行", histLines.length === new Set(histLines).size, `rows=${histLines.length}`);
  await win.screenshot({ path: path.join(__dirname, "verify_pc_hist.png") });

  // 关闭历史 → 存到槽 1
  await win.evaluate(() => document.querySelector("#histClose").click());
  await win.waitForTimeout(400);
  await win.evaluate(() => document.querySelector("#mSave").click());
  await win.waitForTimeout(600);
  await win.evaluate(() => document.querySelectorAll("#slots .slot")[0].click());
  await win.waitForTimeout(600);
  await win.evaluate(() => { const c = document.getElementById("saveClose"); if (c) c.click(); });
  await win.waitForTimeout(300);

  // 返回主界面 → 读档
  await win.evaluate(() => document.querySelector("#mHome").click());
  await win.waitForTimeout(1200);
  check("回到主界面", await win.locator("#btnNew").isVisible());
  await win.click("#btnContinue");
  await win.waitForTimeout(1500);
  const contLine = (await win.locator("#text").innerText()).trim();
  check("读档回到存档句（不跳句）", contLine === curBefore || contLine.includes(curBefore.slice(0, 10)),
    `存:[${curBefore.slice(0, 12)}] 读:[${contLine.slice(0, 12)}]`);
  await win.screenshot({ path: path.join(__dirname, "verify_pc_load.png") });

  // 相册滚动验证
  await win.evaluate(() => localStorage.setItem("aigirls_cg_unlocked", '{"s1":{"cg":"x"},"s2":{"cg":"x"},"s3":{"cg":"x"},"s4":{"cg":"x"},"s5":{"cg":"x"}}'));
  await win.evaluate(() => (location.href = "index.html"));
  await win.waitForTimeout(1800);
  await win.locator("#btnAlbum").click();
  await win.waitForTimeout(700);
  const scrollInfo = await win.evaluate(() => {
    const g = document.getElementById("albumGrid");
    if (!g) return null;
    return { scrollH: g.scrollHeight, clientH: g.clientHeight, overflowY: getComputedStyle(g).overflowY };
  });
  check("相册可滚动", scrollInfo && scrollInfo.scrollH > scrollInfo.clientH, JSON.stringify(scrollInfo));

  await app.close();
  const fails = results.filter(([, ok]) => !ok);
  console.log(`\n===== PC 新构建实测: ${results.length - fails.length}/${results.length} 通过 =====`);
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
