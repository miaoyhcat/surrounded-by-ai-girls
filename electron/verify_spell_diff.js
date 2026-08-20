// 打包版实测：拼字 + 找不同
const { _electron: electron } = require("playwright-core");
(async () => {
  const app = await electron.launch({ executablePath: String.raw`C:\Users\windows\AppData\Local\Programs\surrounded-by-ai-girls\完蛋我被AI娘包围了.exe`, args: [] });
  const win = await app.firstWindow();
  await win.waitForLoadState("domcontentloaded");
  await win.waitForTimeout(2500);
  await win.evaluate(() => localStorage.clear());
  await win.click("#btnNew");
  await win.waitForTimeout(1500);
  const ni = win.locator("#nameInput");
  if (await ni.isVisible()) { await ni.fill("实测君"); await win.click("#nameOk"); await win.waitForTimeout(1500); }
  const tc = win.locator("#titleCard");
  if (await tc.isVisible()) { await tc.click({ force: true }); await win.waitForTimeout(1500); }

  // 拼字（s5b）
  await win.evaluate(() => {
    const si = STORY.findIndex(s => s.id === "s5b");
    const ci = STORY[si].lines.findIndex(l => l.t === "minigame");
    sceneIdx = si; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
    document.getElementById("titleCard").style.display = "none";
    startMinigame(STORY[si].lines[ci]);
  });
  await win.waitForTimeout(400);
  console.log("拼字开场:", await win.evaluate(`document.getElementById('minigame').style.display === 'flex'`) ? "PASS" : "FAIL");
  await win.click("#minigame");
  await win.waitForTimeout(400);
  const spellShown = await win.evaluate(`document.getElementById('mgSpellArea').style.display === 'flex'`);
  console.log("拼字区:", spellShown ? "PASS" : "FAIL");
  await win.evaluate(`(() => {
    const chars = Array.from(MG.intro.sentence);
    const pool = document.querySelectorAll('#mgSpellPool .ch');
    for (const ch of chars) {
      const el = Array.from(pool).find(e => e.style.visibility !== 'hidden' && e.textContent === ch);
      if (el) el.click();
    }
  })()`);
  await win.waitForTimeout(600);
  console.log("拼字完成出结果:", await win.evaluate(`document.getElementById('mgResult').style.display === 'flex'`) ? "PASS" : "FAIL");

  // 找不同（s7c）
  await win.evaluate(() => {
    const si = STORY.findIndex(s => s.id === "s7c");
    const ci = STORY[si].lines.findIndex(l => l.t === "minigame");
    sceneIdx = si; lineIdx = ci; startMinigame(STORY[si].lines[ci]);
  });
  await win.waitForTimeout(300);
  await win.click("#minigame");
  await win.waitForTimeout(400);
  const diffShown = await win.evaluate(`document.getElementById('mgDiffArea').style.display === 'flex'`);
  console.log("找不同区:", diffShown ? "PASS" : "FAIL");
  await win.evaluate(`(() => {
    const diffs = MG.intro.diffs;
    const spans = document.querySelectorAll('#mgDiffRight span');
    Array.from(spans).filter((s, i) => diffs.includes(i)).forEach(el => el.click());
  })()`);
  await win.waitForTimeout(600);
  console.log("找完出结果:", await win.evaluate(`document.getElementById('mgResult').style.display === 'flex'`) ? "PASS" : "FAIL");
  await win.screenshot({ path: "final_diff_pc.png" });
  await app.close();
  console.log("===== 打包版拼字/找不同实测完成 =====");
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
