// Wait till the browser is ready to render the game (avoids glitches)
// 适配：iframe 内 RAF 可能不触发（Electron app:// 协议下），加 setTimeout fallback + 防重入
if (!window.__mg2048Started) {
  window.__mg2048Started = true;
  var __start2048 = function () {
    if (window.__mg2048Ran) return; // 防重入
    window.__mg2048Ran = true;
    new GameManager(4, KeyboardInputManager, HTMLActuator, LocalStorageManager);
  };
  window.requestAnimationFrame(__start2048);
  setTimeout(__start2048, 500); // fallback：RAF 未触发时兜底启动
}
