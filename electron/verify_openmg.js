// 打包版实测：app:// 协议 + 开源小游戏嵌入
const { _electron: electron } = require("playwright-core");
(async () => {
  const app = await electron.launch({ executablePath: String.raw`C:\Users\windows\AppData\Local\Programs\surrounded-by-ai-girls\完蛋我被AI娘包围了.exe`, args: [] });
  const win = await app.firstWindow();
  await win.waitForLoadState("domcontentloaded");
  await win.waitForTimeout(3000);
  const url = await win.evaluate(() => location.href);
  console.log("主页面协议:", url.startsWith("app://") ? "PASS (app://)" : "FAIL (" + url + ")");
  // 进游戏
  await win.evaluate(() => localStorage.clear());
  await win.click("#btnNew");
  await win.waitForTimeout(1800);
  const ni = win.locator("#nameInput");
  if (await ni.isVisible()) { await ni.fill("实测君"); await win.click("#nameOk"); await win.waitForTimeout(1500); }
  const tc = win.locator("#titleCard");
  if (await tc.isVisible()) { await tc.click({ force: true }); await win.waitForTimeout(1500); }
  // 跳 s1 minigame
  await win.evaluate(() => {
    const ci = STORY[0].lines.findIndex(l => l.t === "minigame");
    sceneIdx = 0; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
    document.getElementById("titleCard").style.display = "none";
    startMinigame(STORY[0].lines[ci]);
  });
  await win.waitForTimeout(400);
  console.log("开场卡:", await win.isVisible("#mgIntro") ? "PASS" : "FAIL");
  await win.click("#minigame");
  await win.waitForTimeout(2500);
  // iframe 内 2048 棋盘（app:// 下 ES module 应可加载）
  const frameOk = await win.evaluate(`(() => {
    const f = document.getElementById('mgFrame');
    if (!f || !f.contentDocument) return 'no-frame-doc';
    const doc = f.contentDocument;
    return {
      tiles: doc.querySelectorAll('.tile-container .tile').length,
      grid: !!doc.querySelector('.grid-container'),
      bodyLen: doc.body ? doc.body.innerText.length : 0,
      title: doc.title
    };
  })()`);
  console.log("2048 棋盘:", JSON.stringify(frameOk));
  const tileCount = frameOk.tiles || 0;
  console.log("棋盘加载:", tileCount >= 2 ? "PASS" : "FAIL", "tiles=" + tileCount);
  await win.screenshot({ path: "final_openmg_pc.png" });
  // 点继续
  await win.click("#mgDone");
  await win.waitForTimeout(400);
  console.log("继续剧情:", await win.evaluate(`document.getElementById('minigame').style.display === 'none'`) ? "PASS" : "FAIL");
  await app.close();
  console.log("===== 打包版开源小游戏实测完成 =====");
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
