// preload.js — 通过 contextBridge 安全暴露系统信息给游戏页面
// （渲染进程 contextIsolation 开启，游戏页面只能通过 window.pcInfo 读取）
const { contextBridge } = require("electron");
const os = require("os");

function cleanCpuModel(model) {
  if (!model) return null;
  // 去掉 "(R)" "(TM)" "@ 3.60GHz" 等噪音，保留 "Intel Core i7-12700H" 这类
  return String(model)
    .replace(/\(R\)/g, "")
    .replace(/\(TM\)/g, "")
    .replace(/\(C\)/g, "")
    .replace(/@\s*[\d.]+GHz/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

contextBridge.exposeInMainWorld("pcInfo", {
  cpuModel: (() => {
    try {
      const cpus = os.cpus();
      return cpus && cpus.length ? cleanCpuModel(cpus[0].model) : null;
    } catch (e) { return null; }
  })(),
  cpuCount: (() => {
    try { return os.cpus().length; } catch (e) { return null; }
  })(),
  totalMemBytes: (() => {
    try { return os.totalmem(); } catch (e) { return null; }
  })(),
  platform: (() => {
    try { return process.platform; } catch (e) { return null; }
  })(),
  release: (() => {
    try { return os.release(); } catch (e) { return null; }
  })(),
});
