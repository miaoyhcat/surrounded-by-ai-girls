# 《完蛋，我被 AI 娘包围了》

> AI 娘校园恋爱喜剧 · 共通线 + 三条个人线 + 10 结局 · 目标平台 Web → Steam
> 英文名提案：**Surrounded by AI Girls**（Steam 商店用）
> 项目状态：**剧本/美术方案定稿中，引擎待开发**

## 一句话

2022 到 2026，一个普通大学生被接二连三的"转学生"搅得天翻地覆：万能生徒会长 GPT 娘、傲娇伦理委员长 Claude 娘、特困生技术宅鲸鱼娘。白天是同学，晚上是聊天窗口里的常客。毕业前，你必须决定带走谁——或者，谁都不选。

## 核心设定

- **换工具不换人**：Codex、Claude Code、OpenClaw 换来换去，背后调用的永远是同一位她——感情就是一次次 API 调用累积出来的
- **真实 AI 史为暗线**：2022 ChatGPT 破壳 → 2023 GPT-4/宫斗/百模大战 → 2024 Sora/Claude 3/Her 时刻 → 2025 DeepSeek 屠榜/编程元年 → 2026 OpenClaw 浪潮
- **玩法**：聊天窗口式自由对话（LLM 驱动）+ 章节选项 + 羁绊值 + 10 结局图鉴 + 语音（每娘一声线）

## 目录结构

```
ai-galgame/
├── README.md                 # 本文件
├── docs/
│   ├── outline.md            # 剧情大纲（v1.3）
│   ├── art_plan.md           # 美术管线方案
│   ├── cg_list.md            # CG 插画清单（给画师）
│   ├── research/             # 形象调研存档（B站流传形象参考图）
│   └── steam/
│       └── steam_launch_plan.md  # Steam 上架规划（AI 披露/物料/定价）
├── assets/                   # ★ 美术资源（画师产出放这里）
│   ├── characters/           # 角色立绘（whale/ gpt/ claude/ 各一目录）
│   │   └── _placeholder_svg/ # 早期 SVG 占位稿（已废弃，仅存档）
│   ├── cg/                   # 剧情 CG
│   ├── ui/                   # UI 素材（图标/框体/按钮）
│   ├── icon.png              # 游戏图标 ← 画师第一张产出
│   └── audio/                # BGM/音效（music-maker 管线）
├── src/
│   ├── server/               # 后端：FastAPI + DeepSeek + edge-tts
│   │   └── server.py
│   ├── web/                  # 前端：聊天窗口/桌面场景（静态页）
│   │   └── static/
│   └── data/                 # 剧情数据（角色卡/章节剧本/结局表）
├── scripts/                  # 工具脚本（打包/部署/素材检查）
└── build/                    # 打包产物（Steam 用 Electron 包）
```

## 资源接入约定（重要）

- 画师产出 → 丢进 `assets/` 对应目录（立绘 `characters/<id>/`，CG `cg/`，图标 `icon.png`）
- 推荐规格：头像 PNG 透明底 ≥1024px 竖版 3:4；CG 横版 16:9 ≥1920 宽；图标 ≥512px
- 文件就位后游戏自动使用（文件名约定见 `docs/art_plan.md`）

## 当前状态

- [x] 剧情大纲 v1.3（角色立体化 + 10 结局 + Codex/Claude Code）
- [x] 美术管线方案 + 形象基准（鲸鱼尾鳍/花环/星芒）
- [x] Steam 上架规划
- [ ] 图标/立绘/CG（画师进行中）
- [ ] 游戏引擎（对话/羁绊/结局/存档）
- [ ] 聊天界面 + 桌面场景
- [ ] Web 试玩版 → Steam 打包

## 密钥铁律

- 任何 API key 只走环境变量，绝不进仓库（见 .gitignore）
- 生图只用 Seedream；视觉分析可用 GLM-4.5（免费）
