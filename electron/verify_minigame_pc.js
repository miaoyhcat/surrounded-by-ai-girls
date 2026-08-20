// 打包版实测：PC 背景恢复 + 小游戏流程
const { _electron: electron } = require("playwright-core");
(async () => {
  const app = await electron.launch({ executablePath: String.raw`C:\Users\windows\AppData\Local\Programs\surrounded-by-ai-girls\完蛋我被AI娘包围了.exe`, args: [] });
  const win = await app.firstWindow();
  await win.waitForLoadState("domcontentloaded");
  await win.waitForTimeout(2500);
  // 1. 主界面背景 = center/contain（PC 恢复原样）
  const bg = await win.evaluate(() => {
    const el = document.querySelector(".hallbg");
    const cs = getComputedStyle(el);
    return { pos: cs.backgroundPosition, size: cs.backgroundSize };
  });
  console.log("PC背景:", JSON.stringify(bg), bg.pos === "50% 50%" && bg.size === "contain" ? "PASS" : "FAIL");
  // 2. 进游戏测小游戏流程
  await win.evaluate(() => localStorage.clear());
  await win.click("#btnNew");
  await win.waitForTimeout(1500);
  const ni = win.locator("#nameInput");
  if (await ni.isVisible()) { await ni.fill("实测君"); await win.click("#nameOk"); await win.waitForTimeout(1500); }
  const tc = win.locator("#titleCard");
  if (await tc.isVisible()) { await tc.click({ force: true }); await win.waitForTimeout(1500); }
  await win.evaluate(() => {
    const ci = STORY[0].lines.findIndex(l => l.t === "minigame");
    sceneIdx = 0; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
    document.getElementById("titleCard").style.display = "none";
    startMinigame(STORY[0].lines[ci]);
  });
  await win.waitForTimeout(400);
  const mgOpen = await win.evaluate(`document.getElementById('minigame').style.display === 'flex'`);
  console.log("小游戏打开:", mgOpen ? "PASS" : "FAIL");
  await win.click("#minigame");
  await win.waitForTimeout(500);
  const bubble = await win.evaluate(`document.querySelectorAll('.mg-bubble').length > 0`);
  console.log("气泡出现:", bubble ? "PASS" : "FAIL");
  if (bubble) { await win.click(".mg-bubble >> nth=0"); await win.waitForTimeout(200); }
  const score = await win.evaluate("MG.score");
  console.log("点击计分:", score > 0 ? "PASS" : "FAIL", "score=" + score);
  await win.screenshot({ path: "final_minigame_pc.png" });
  await app.close();
  console.log("===== 打包版实测完成 =====");
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
