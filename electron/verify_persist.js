// 关机重启持久化验证：
// 1. 启动 exe → 推进剧情 → 存档到槽位
// 2. 完全退出（模拟关机）
// 3. 重新启动 exe → 检查存档槽内容 / 继续游戏是否可用
// 用解压版 exe（userData 与安装版同路径，验证 Electron localStorage 磁盘持久化）
const { _electron: electron } = require("playwright-core");
const fs = require("fs");
const os = require("os");

const EXE = String.raw`C:\Users\windows\Desktop\完蛋我被AI娘包围了-免安装zip版\完蛋我被AI娘包围了.exe`;
const results = [];
function check(name, cond, extra = "") {
  results.push([name, !!cond]);
  console.log((cond ? "PASS  " : "FAIL  ") + name + (extra ? "  | " + extra : ""));
}

async function bootOnce() {
  const app = await electron.launch({ executablePath: EXE, args: [] });
  const win = await app.firstWindow();
  await win.waitForLoadState("domcontentloaded");
  await win.waitForTimeout(2000);
  return { app, win };
}

(async () => {
  // 第一步：启动并写入存档
  const { app, win } = await bootOnce();
  // 清掉旧状态，开新游戏到剧情中，存到槽位 1
  await win.evaluate(() => localStorage.clear());
  await win.waitForTimeout(300);
  await win.click("#btnNew");
  await win.waitForTimeout(1500);
  const ni = win.locator("#nameInput");
  if (await ni.isVisible()) {
    await ni.fill("重启君");
    await win.click("#nameOk");
    await win.waitForTimeout(1500);
  }
  const tc = win.locator("#titleCard");
  if (await tc.isVisible()) { await tc.click({ force: true }); await win.waitForTimeout(1500); }
  // 推进几句
  for (let i = 0; i < 5; i++) {
    await win.waitForFunction("!window.__iv", null, { timeout: 5000 }).catch(()=>{});
    await win.click("#boxInner");
    await win.waitForTimeout(350);
  }
  const markerText = (await win.locator("#text").innerText()).trim().slice(0, 20);
  // 打开菜单存档到槽位 1
  await win.evaluate(() => document.querySelector("#menuBtn").click());
  await win.waitForTimeout(400);
  await win.evaluate(() => document.querySelector("#mSave").click());
  await win.waitForTimeout(600);
  await win.evaluate(() => document.querySelectorAll("#slots .slot")[0].click());
  await win.waitForTimeout(700);
  // 检查槽位是否有内容
  const slotInfo = await win.evaluate(() => {
    const raw = localStorage.getItem("aigirls_save_v1_0");
    return raw ? JSON.parse(raw) : null;
  });
  check("槽位 1 已存档", slotInfo && slotInfo.scene !== undefined, `scene=${slotInfo && slotInfo.scene}`);
  // 记录存档快照
  const snapshot = JSON.stringify(slotInfo);
  fs.writeFileSync(__dirname + "/persist_snapshot.json", snapshot);
  console.log("  存档快照已写:", snapshot.slice(0, 120));
  await app.close(); // 完全退出 = 模拟关机
  console.log("  已完全退出（模拟关机重启）\n");

  // 第二步：重新启动，验证存档还在
  await new Promise(r => setTimeout(r, 1500));
  const { app: app2, win: win2 } = await bootOnce();
  const slot2 = await win2.evaluate(() => {
    const raw = localStorage.getItem("aigirls_save_v1_0");
    return raw ? JSON.parse(raw) : null;
  });
  check("重启后槽位 1 存档仍在", !!slot2, slot2 ? `scene=${slot2.scene}` : "EMPTY");
  check("存档内容一致", slot2 && JSON.stringify(slot2) === fs.readFileSync(__dirname + "/persist_snapshot.json", "utf8"));
  // 继续游戏按钮应可用
  const contVisible = await win2.locator("#btnContinue").isVisible();
  const contClickable = await win2.evaluate(() => {
    const b = document.getElementById("btnContinue");
    return b && getComputedStyle(b).display !== "none";
  });
  check("「继续游戏」可用", contVisible && contClickable);
  await win2.click("#btnContinue");
  await win2.waitForTimeout(1800);
  const resumed = (await win2.locator("#text").innerText()).trim();
  check("继续游戏成功进入剧情", resumed.length > 0, resumed.slice(0, 20));
  await win2.screenshot({ path: __dirname + "/persist_verify.png" });
  await app2.close();

  const fails = results.filter(([, ok]) => !ok);
  console.log(`\n===== 重启持久化: ${results.length - fails.length}/${results.length} 通过 =====`);
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
