// electron-builder afterPack 钩子：瘦身——删除多余 Chromium 语言包，只留中英文
exports.default = async function (context) {
  const fs = require("fs");
  const path = require("path");
  const localeDir = path.join(context.appOutDir, "locales");
  if (!fs.existsSync(localeDir)) return;
  let removed = 0;
  for (const f of fs.readdirSync(localeDir)) {
    // 保留 zh-CN（中文）与 en-US（英文）语言包，其余删除
    if (!f.startsWith("zh-CN") && !f.startsWith("en-US")) {
      fs.unlinkSync(path.join(localeDir, f));
      removed++;
    }
  }
  console.log(`[afterPack] locales 瘦身: 删除 ${removed} 个语言包`);
};
