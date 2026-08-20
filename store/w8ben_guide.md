# W-8BEN 税务表填写指南（中国个人开发者）

> W-8BEN 是给**非美国个人**填的税务表格，声明你不是美国纳税人、且适用美中税务条约。
> 全程约 10 分钟，逐项对照填。

## 逐项填写（表单是英文，这里是中文对照）

| 表格字段 | 填什么 | 示例 |
|---|---|---|
| **1. Name**（姓名） | 姓名拼音，与护照一致 | WANG XIAOMING |
| **2. Country of incorporation** | 不适用（个人）| — |
| **3. Type of beneficial owner** | 选 **Individual**（个人）| — |
| **4. Permanent residence address**（常住地址） | 身份证/护照上的中国地址（拼音）| ROOM 501, XX ROAD, BEIJING, CHINA |
| **5. Mailing address** | 同 4（若不同再填）| — |
| **6. U.S. taxpayer identification number** | **留空**（你没有美国 TIN）| — |
| **7. Foreign tax identifying number**（外国税号） | 填**你的中国身份证号**（18 位）| 110101199001011234 |
| **8. Reference number** | 留空 | — |
| **9. Date of birth** | 出生日期（格式 MM/DD/YYYY）| 01/01/1990 |
| **Part II. Claim of Tax Treaty Benefits**（条约减免） | | |
| **9a. Treaty country** | **CHINA**（中国）| |
| **9b. Treaty article** | **Article 12（版税 Royalties）**——游戏销售分成属于版税 | |
| **9c. Limitation on Benefits** | 选 **"Yes, I am a resident of the treaty country"**（你是中国税收居民）| |
| **Part III** | 中国无美国常设机构，选 **"No"** | |
| **Part IV. Sign here**（签名） | 电子签名：姓名拼音 + 日期，勾选同意 | |

## 关键解释（为什么这么填）
- **中国是美中税务条约国**：条约让中国居民的版税收入在美国预扣税率降为 **0%（或很低）**——不填条约条款就会被扣 30%！
- **游戏销售分成属于"版税/特许权使用费"（Royalties）**，所以用 Article 12
- **身份证号 = 你的中国税号（TIN）**，Valve 接受；如果系统校验不通过，会提示你申请 ITIN（流程较长，但一般身份证号都能过）

## 填写后的预期
- 提交后 Valve 会显示税务状态 **"US Tax Treaties" / 0% withholding** 之类
- 此后 Valve 每月结算打款时**不预扣美国税**，你拿 100% 分成（国内个税自己报）

## ⚠️ 如果卡住
1. TIN 校验失败 → 截屏发我，走 ITIN 申请流程（免费，需填 W-7 表 + 护照复印件寄美国 IRS，约 6-12 周）
2. 看不懂某个字段 → 截屏发我，逐字段翻译
