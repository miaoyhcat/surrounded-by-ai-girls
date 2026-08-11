# 游戏开发工具调研（GitHub 淘金结果）

> 2026-08-11 · 调研目标：视觉小说引擎 / Steam 接入 / 2D 动画 / 美术工具
> 结论先行：**引擎自研（聊天窗口玩法）+ OpenWebGAL 做演出参考 + PixiJS/DragonBones 做小娘动画 + Greenworks 上 Steam + LibreSprite 给画师**

## 一、引擎（视觉小说）

| 项目 | ⭐ | 结论 |
|---|---|---|
| **OpenWebGAL/WebGAL** | 3.9k | **强烈推荐研究**：国产开源网页视觉小说引擎，可视化编辑器，演出/语音/存档齐全。关键证据：官方展示游戏《Elf of Era Idols Project》**已通过 Steam 发行**——证明"网页引擎→Steam"路线可行。我们的聊天窗口玩法需自研 UI，但它的章节卡/打字机/存档/演出系统全部可参考移植 |
| renpy/renpy | 27k+ | 桌面 VN 标准引擎（Python），成熟但 UI 定制成本高（聊天窗口玩法不适合）。作为对照参考 |
| Monogatari/Monogatari | 4.4k | 老牌网页 VN 引擎（JS），支持自定义 UI，备选 |
| VoidMatrixHeathcliff/VoidNovelEngine | - | 另一个网页 VN 引擎，备选 |
| KirikiriTools | - | 吉里吉里（经典日系 VN 引擎）工具链，考古参考 |

**决策**：聊天窗口玩法 = 自研（已在做 server.py + 前端）；OpenWebGAL 的**开源代码**用来抄演出方案（打字机、选项演出、存档格式、语音同步）。

## 二、Steam 接入（Electron 版必装）

| 项目 | 说明 |
|---|---|
| **Cecil0o0/Greenworks** | Electron 接入 Steamworks 的标准方案（成就/云存档/Workshop/覆盖层）。Steam 上架的 Electron 游戏主流选择。构建期装，运行时必须有 Steam 环境 |

## 三、2D 动画（小娘在键盘上跑！）

| 项目 | 说明 |
|---|---|
| **pixijs/pixijs** | 网页 2D 渲染引擎。**小娘在键盘上跑酷 = 精灵动画**，PixiJS 负责：走路帧循环、跳跃、在键帽间移动的坐标逻辑、与聊天 UI 叠加 |
| **DragonBones/DragonBonesJS** | 免费骨骼动画（国产，Egret 出品），JS 运行时原生支持 PixiJS——**Q 版小娘的挥手/比 V/被吓一跳**这类动作用骨骼动画做，表情/动作可复用 |
| EsotericSoftware/spine-runtimes | 骨骼动画行业标准，但编辑器收费（专业版），备选 |
| **LibreSprite/LibreSprite** | 8.2k⭐ 免费开源像素画工具（Aseprite 免费分支）：图层/帧/洋葱皮/实时动画预览——**给画师画小娘跑动帧用** |
| Orama-Interactive/Pixelorama | 另一个免费开源像素画编辑器，备选 |

## 四、美术素材（免费可商用）

| 项目 | 说明 |
|---|---|
| KenneyNL 系列 | 免费游戏素材库（UI/音效/图标/几何），非动漫风但 UI/音效可白嫖 |
| OpenGameArt（非 GitHub） | 免费游戏素材站，社区质量参差 |
| 无版权 Q 版动漫素材 | GitHub 上基本没有现成的高质量 Q 版动漫素材——**Q 版小人必须画师原创**（我们正好有画师），动画化交给 DragonBones/LibreSprite |

## 五、AI 对话（已有管线，备用参考）

- 自研：DeepSeek + edge-tts（已完成）
- 备选参考：无需引入，保持自研控制力

## 下一步（推荐顺序）

1. **读 OpenWebGAL 源码**：抄演出/存档/选项实现 → 融入我们的聊天引擎
2. **PixiJS 集成**：小娘精灵系统（走路/跳跃/停留锚点=键帽坐标）
3. **DragonBones** 给画师：教她导骨骼动画（或先用 LibreSprite 做帧动画，简单直接）
4. **Greenworks**：打包阶段接入（Steam 云存档 = 羁绊进度同步）
