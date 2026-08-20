// 完蛋，我被AI娘包围了 — Electron 主进程
const { app, BrowserWindow, Menu, protocol, net } = require("electron");
const path = require("path");
const { pathToFileURL } = require("url");

// 自定义协议 app:// 服务游戏资源目录（file:// 下 ES module 会触发 CORS 拦截，
// 开源小游戏（snake/tetris 等）依赖 ES module 加载，必须走 http 语义的协议）
// 需在 app ready 前声明特权：standard（可用 localStorage）+ secure
protocol.registerSchemesAsPrivileged([
  { scheme: "app", privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true } }
]);

function registerAppProtocol() {
  const root = path.join(__dirname, "game");
  protocol.handle("app", (request) => {
    const url = new URL(request.url);
    let rel = decodeURIComponent(url.pathname);
    if (rel === "/" || rel === "") rel = "/index.html";
    const filePath = path.normalize(path.join(root, rel));
    // 防止路径逃逸到目录外
    if (!filePath.startsWith(root)) return new Response("Forbidden", { status: 403 });
    return net.fetch(pathToFileURL(filePath).toString());
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1360,
    height: 880,
    minWidth: 960,
    minHeight: 640,
    icon: path.join(__dirname, "build", "icon.ico"),
    title: "完蛋，我被AI娘包围了",
    autoHideMenuBar: true,
    backgroundColor: "#0B1020",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false, // 允许 preload 使用 os 模块读取 CPU/内存信息（contextIsolation 仍开启，安全）
      preload: path.join(__dirname, "preload.js") // 暴露系统信息（CPU 型号/内存等）给游戏
    }
  });

  win.setMenuBarVisibility(false);
  win.loadURL("app://game/index.html");

  // 允许本地页面跳转（index ↔ game），拦截外部导航/拖拽
  win.webContents.on("will-navigate", (e, url) => {
    if (!url.startsWith("app://")) e.preventDefault();
  });
  // 游戏内官网链接 → 系统浏览器打开
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("http://") || url.startsWith("https://")) {
      require("electron").shell.openExternal(url);
    }
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  registerAppProtocol();
  Menu.setApplicationMenu(null);
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
