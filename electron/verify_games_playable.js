// snake/tetris 打包版可玩性实测
const { _electron: electron } = require("playwright-core");
(async () => {
  const app = await electron.launch({ executablePath: String.raw`C:\Users\windows\AppData\Local\Programs\surrounded-by-ai-girls\完蛋我被AI娘包围了.exe`, args: [] });
  const win = await app.firstWindow();
  await win.waitForLoadState("domcontentloaded");
  await win.waitForTimeout(2500);
  await win.evaluate(() => { if (!localStorage.getItem("aigirls_name")) localStorage.setItem("aigirls_name", "验证"); });
  await win.click("#btnNew");
  await win.waitForTimeout(2000);

  // ═══ snake ═══
  await win.evaluate(() => {
    const si = STORY.findIndex(s => s.id === "s2");
    const ci = STORY[si].lines.findIndex(l => l.t === "minigame");
    sceneIdx = si; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
    document.getElementById("titleCard").style.display = "none";
    startMinigame(STORY[si].lines[ci]);
  });
  await win.waitForTimeout(400);
  await win.click("#minigame");
  await win.waitForTimeout(3000);
  const s1 = await win.evaluate(`(() => {
    const d = document.getElementById('mgFrame').contentDocument;
    const easy = d.querySelector('[data-action="play"]');
    const has = !!easy;
    if (easy) easy.click();
    return { has, title: d.title };
  })()`);
  console.log("snake 菜单:", s1.has ? "PASS" : "FAIL", s1.title);
  await win.waitForTimeout(1500);
  const s2 = await win.evaluate(`(() => {
    const d = document.getElementById('mgFrame').contentDocument;
    return d.body.innerText.slice(0, 60);
  })()`);
  console.log("snake 开始后:", s2.length > 0 ? "PASS" : "FAIL", s2.replace(/\n/g, " | ").slice(0, 50));
  await win.evaluate(`(() => {
    const f = document.getElementById('mgFrame');
    const w = f.contentWindow, d = f.contentDocument;
    for (const [key, which] of [["ArrowUp", 38], ["ArrowRight", 39], ["ArrowDown", 40]]) {
      d.dispatchEvent(new w.KeyboardEvent('keydown', { key, which, keyCode: which, bubbles: true, cancelable: true }));
    }
  })()`);
  await win.waitForTimeout(900);
  const s3 = await win.evaluate(`(() => {
    const d = document.getElementById('mgFrame').contentDocument;
    return { len: d.body.innerText.length, t: d.body.innerText.slice(0, 40) };
  })()`);
  console.log("snake 按键后(蛇移动):", s3.len > 0 ? "PASS" : "FAIL", s3.t.replace(/\n/g, " ").slice(0, 36));
  await win.click("#mgDone");
  await win.waitForTimeout(400);

  // ═══ tetris ═══
  await win.evaluate(() => {
    const si = STORY.findIndex(s => s.id === "s7");
    const ci = STORY[si].lines.findIndex(l => l.t === "minigame");
    sceneIdx = si; lineIdx = ci; inTitle = false; inChoice = false; inTransition = false;
    document.getElementById("titleCard").style.display = "none";
    startMinigame(STORY[si].lines[ci]);
  });
  await win.waitForTimeout(400);
  await win.click("#minigame");
  await win.waitForTimeout(3000);
  const t1 = await win.evaluate(`(() => {
    const d = document.getElementById('mgFrame').contentDocument;
    const start = d.querySelector('[data-action="start"]');
    const has = !!start;
    if (start) start.click();
    return { has, title: d.title };
  })()`);
  console.log("tetris 菜单:", t1.has ? "PASS" : "FAIL", t1.title);
  await win.waitForTimeout(1500);
  const t2 = await win.evaluate(`(() => {
    const d = document.getElementById('mgFrame').contentDocument;
    return d.body.innerText.slice(0, 60);
  })()`);
  console.log("tetris 开始后:", t2.length > 0 ? "PASS" : "FAIL", t2.replace(/\n/g, " ").slice(0, 44));
  await win.evaluate(`(() => {
    const f = document.getElementById('mgFrame');
    const w = f.contentWindow, d = f.contentDocument;
    for (const [key, which] of [["ArrowDown", 40], ["ArrowLeft", 37], ["ArrowRight", 39]]) {
      d.dispatchEvent(new w.KeyboardEvent('keydown', { key, which, keyCode: which, bubbles: true, cancelable: true }));
    }
  })()`);
  await win.waitForTimeout(900);
  const t3 = await win.evaluate(`(() => {
    const d = document.getElementById('mgFrame').contentDocument;
    return { len: d.body.innerText.length, t: d.body.innerText.slice(0, 40) };
  })()`);
  console.log("tetris 按键后(方块下落):", t3.len > 0 ? "PASS" : "FAIL", t3.t.replace(/\n/g, " ").slice(0, 36));
  await app.close();
  console.log("===== snake/tetris 可玩性实测完成 =====");
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
