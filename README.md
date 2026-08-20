# 《完蛋，我被AI娘包围了》🎮

**键盘同居恋爱喜剧 · 独立开发 Galgame**（Windows / Android）

> 2022 年的冬夜，你打开了那个"据说什么都会"的 AI 聊天框。
> 从此，你的键盘上住进了三个"AI娘"——
> 她们会吃错字、会记仇、会在你熬夜时把屏幕调暗，
> 然后在你毕业那天，问你：**"明天，我们住哪？"**

---

## 🎯 游戏介绍

- **类型**：剧情向恋爱喜剧 Galgame（分支选择 + 多结局）
- **平台**：Windows（Electron）/ Android（Capacitor，横屏）
- **内容**：
  - 📖 15 个章节 · 660+ 句全配音台词
  - 🎙️ 三角色独立配音（GPT娘 / 鲸鱼娘 / Claude娘）
  - 🎨 21 张剧情 CG · 回忆相册
  - 🕹️ 3 个内置小游戏（贪吃蛇 / 2048 / 俄罗斯方块）
  - 💾 3 槽手动存档 + 自动存档 · 历史回跳
  - 🎵 多首 BGM + 音效
- **开发者**：独立一人完成（剧情 / 配音 / 美术 / 前后端）

## 🖥️ 运行方式

### 直接玩（推荐）
- **Windows**：下载 [Release](https://github.com/miaoyhcat/surrounded-by-ai-girls/releases) 中的 `AI-Girls-Windows-v0.1.0.zip`，解压后运行 `完蛋我被AI娘包围了.exe`
- **Android**：下载 [Release](https://github.com/miaoyhcat/surrounded-by-ai-girls/releases) 中的 `AI-Girls-Android-v0.1.0.apk` 直接安装（包名 `com.aigirls.galgame`，横屏）

### 从源码运行（网页版）
```bash
cd src/web/demo
python -m http.server 8899
# 浏览器打开 http://127.0.0.1:8899/
```

## 📂 项目结构

```
src/web/demo/    网页版游戏源码（纯 HTML/CSS/JS，零依赖）
  ├── index.html   主菜单（开始/继续/相册/设置/赞赏）
  ├── game.html    游戏引擎（剧情/配音/存档/小游戏）
  ├── data.js      全部剧情数据（15 章 660+ 行台词）
  ├── assets/      CG 立绘与图片
  ├── voice/       三角色配音（662 句 mp3）
  ├── audio/       BGM 与音效
  └── minigames/   内置小游戏（开源嵌入）
electron/         Windows 打包工程（Electron）
mobile/           Android 打包工程（Capacitor）
tools/            开发工具脚本（TTS 合成/音频处理/测试）
```

## 🛠️ 技术栈

- 前端：原生 HTML/CSS/JS（零依赖，可直接运行）
- PC 打包：Electron
- Android 打包：Capacitor 6
- 配音：IndexTTS-2.5（B 站开源 TTS）+ faster-whisper 质检
- 参考音色：可莉（鲸鱼娘）/ 卡齐娜（GPT娘）/ 琳妮特（Claude娘）

## 📜 版权与开源

- 本游戏所用素材来自网络与各大开源项目，如有版权问题请联系：2233873332@qq.com
- 配音为 TTS 合成，参考音色仅用于角色演绎
- [隐私政策](privacy.html)

## 💬 联系与反馈

- 邮箱：2233873332@qq.com
- 欢迎 Star / Issue / 分享给朋友！

---

**—— 高中生独立研发，感谢你的支持 ❤️**
