# 配音 / BGM 接入说明（v4.1）

> 2026-08-11 · 为 exe 版加入：角色配音（ChatTTS 本地生成）+ 背景音乐（魔王魂免费钢琴曲）+ 设置面板

## 角色配音（ChatTTS）

- 模型：ChatTTS 0.2.5（开源，中文自然度高，带语气/停顿，非播音腔）
- 音色：固定随机种子 → 固定音色
  - GPT娘：seed=42（活泼，语速 [speed_5]）
  - 鲸鱼娘：seed=888（冷静，语速 [speed_4]）
- 数量：**275 条** = GPT娘 192 + 鲸鱼娘 83（g 台词 189 + whale 台词 73 + 补齐）
- 位置：`src/web/demo/voice/`（g_N.mp3 / whale_N.mp3，128kbps mp3，共 17MB）
- 编号规则：按 STORY 遍历顺序，g / whale 各自从 1 递增（与 `game.html` 的 `buildVoiceMap()` 一致）
- 生成脚本：`tools/gen_voice.py`（GPU 生成约 22 分钟 / 278 条）
  - 文本清洗：去掉 `(小声)` `（纸条）` 等舞台指示、`「」` 引号；保留 `……` `——` 停顿
  - 断点续跑：`python tools/gen_voice.py --start N`
- 依赖环境（踩坑记录）：
  - Python 3.12 + torch 2.9.1+cu128（RTX 5060，Blackwell 需 torch≥2.7）
  - torch 需从阿里镜像下载 wheel 本地安装：`mirrors.aliyun.com/pytorch-wheels/cu128/`
  - torchaudio / torchvision 必须同版本 `+cu128` 且用 `--no-deps` 安装（防止 pip 降级 torch）
  - transformers 必须 **4.46.3 以下**（4.49+ 的 modeling_utils 会 import torchvision → 本机 torchvision C 扩展 ABI 崩）
  - 模型下载走 hf-mirror：`HF_ENDPOINT=https://hf-mirror.com`

## 背景音乐（BGM）

- 来源：**魔王魂**（maou.audio，免费商用，森田交一 作曲）—— 非 AI 生成，满足"不要你自己生成"
- 曲目：`audio/bgm_piano36/38/40/41.mp3`（温柔钢琴，60-140 秒循环）
  - 默认曲目 Ⅰ = piano41（85s，轻柔）
- 下载方式：直链 `https://maou.audio/sound/bgm/maou_bgm_piano{NN}.mp3`，需带 Referer 头
- 许可：魔王魂规则允许免费商用（免费曲目无需署名，禁止转售/二次配布素材本身）

## 设置面板（game.html 内菜单 → ⚙ 设置）

- 背景音乐：开/关 + 音量滑条 + 曲目切换（4 首）
- 角色配音：开/关（GPT娘 / 鲸鱼娘）
- 设置持久化：localStorage `aigirls_settings`
- BGM 自动播放策略：首次用户点击（标题卡/任意推进）后启动

## 自动播放速度（v4.1 调慢）

- 打字：2 字/26ms → **1 字/34ms**
- 行间隔：2400ms → **3600ms**；转场：2600ms → **4200ms**
- 配音开启时：自动播放**等当前语音播完**再进下一行（+700ms 缓冲）

## 历史记录回档

- 每条历史记录携带位置快照（scene / line）
- 点击任意条目 → 跳回该进度：恢复 CG、名字、语音、自动存档
- 回档到 choice / transition 行时恢复对应交互状态

## 剧情衔接（v4.1）

- 幕2→幕3：新增转场（2023.10-12 学会查资料/规划，引出论文周）
- 幕4（鲸鱼娘出场）：新增 12 行铺垫——
  2024 年 AI 大爆炸 → GPT娘 话变少（"我是你一个人的秘密"）→ 室友安利 → GPT娘 主动让玩家去试
  → 深夜打开网页 → 蓝色光 → 鲸鱼娘登场（不再突兀）
- 幕5（高铁）：新增 6 行衔接——鲸鱼娘 问"家"是什么、要跟回家（呼应结尾"过年真好"）
- 幕7（终局）：新增毕业氛围铺垫（答辩结束、宿舍变空）

## 端到端测试

- `tools/e2e_test.py`：21 项全过（标题/推进/选项/自动播放/快进/历史回档/存档读档/设置/BGM/配音/改名/返回主界面/无页面错误）
- 配音补充验证：g_1 / whale_1 播放、配音关闭停播、自动播放等待语音
