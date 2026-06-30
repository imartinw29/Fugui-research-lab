---
name: a-share-research-report
description: A股研究报告自动生成管道 — sector-overview → comps-analysis → PPT。输入行业/标的，输出结构化投研报告（Markdown + PPTX + Excel 数据表）。
category: finance
---

# A股研究报告自动生成（Research Report Pipeline）

> **一句话：** 说一个行业或一只票，自动出行业分析 + 可比估值 + 研报 PPT。

## 触发条件

用户提到以下关键词组合时自动激活：
- "分析一下 XX 行业" / "看看 XX 板块"
- "XX 股票估值怎么样" / "XX 和同行比"
- "出一份 XX 的研报"
- "写个 XX 行业深度"

---

## 管道架构

```
用户输入（行业/标的）
        │
        ▼
┌──────────────────────────┐
│  Phase 0: 预检           │  ← 检查依赖可用性
│  MX_APIKEY / openpyxl / node│
│  通过后进入分析管道          │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Phase 1: 行业分析        │  ← a-share-sector-overview
│  定位申万行业、TAM、格局、资金面  │
│  输出: sector_analysis.md    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Phase 2: 可比公司分析     │  ← a-share-comps-analysis
│  筛选可比组、拉财务数据、跑统计  │
│  输出: comps_analysis.xlsx  │
└──────────┬───────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌──────────┐ ┌──────────────────────┐
│ Phase 3a │ │ Phase 3b (可选，深度)  │ ← a-share-valuation-report
│ 组装 PPT │ │ 个股深度估值报告        │
│          │ │ 隐含PE校验/多方法估值/自洽 │
│          │ │ 输出: valuation_report.md │
└────┬─────┘ └──────────┬───────────┘
     │                  │
     └────────┬─────────┘
              ▼
┌──────────────────────────┐
│  Phase 4: 组装 PPT        │  ← powerpoint skill
│  行业全景 → 估值对标 → 结论   │
│  输出: research_report.pptx │
└──────────────────────────┘
```

**Phase 3b 触发条件：** 用户明确要求对单个标的做估值判断，或说出"估值""值多少""合理吗"等关键词时自动激活。

---

## Phase 0：预检（Pre-flight Check）

在进入分析管道前，先验证依赖可用性：

```python
# 1. 确认 MX_APIKEY 可访问
import os
env_file = os.path.expanduser('~/.hermes/.env')
# 读取并验证 key 存在且长度 > 10

# 2. 确认 openpyxl 可导入
import openpyxl  # 若无，pip install openpyxl --break-system-packages

# 3. 确认 pptxgenjs 可用
# node -e "require('pptxgenjs')"  # 若无，npm install -g pptxgenjs
```

**常见阻断及解决：**

| 阻断 | 现象 | 解决 |
|------|------|------|
| MX_APIKEY 不在沙箱 | `ValueError: MX_APIKEY 未设置` | 手动读取 `.env` 文件传递 api_key（见 `dfcf-finance-tool` skill 的 execute_code 沙箱章节） |
| openpyxl 未安装 | `ModuleNotFoundError: openpyxl` | `pip install openpyxl --break-system-packages` |
| pptxgenjs 未安装 | `Cannot find module 'pptxgenjs'` | `npm install -g pptxgenjs`；运行时设 `NODE_PATH=$(npm root -g)` |
| markitdown 未安装 | — | 非阻断项，可跳过文本 QA |

**运行策略：** 对于需要 3+ 次 API 调用的场景，优先用 `terminal()` 运行完整 Python 脚本而非 `execute_code()`——terminal 环境默认加载 `.env`，避免手动传 key。

---

## Phase 1：行业分析（`a-share-sector-overview`）

**触发条件：** 用户指定行业或主题。

**输入：** 行业关键词（如"半导体"、"光伏"、"AI算力"）
**输出：** `./out/sector_analysis.md`

**执行步骤：**

1. 加载 `a-share-sector-overview` skill
2. 用 `dfcf-finance-tool` 获取板块行情、资金流向
3. 按 sector-overview 框架写 Markdown 分析
4. 提炼 PPT 所需关键数据：
   - 板块涨跌幅、PE 分位、北向趋势
   - CR5 集中度、龙头名单
   - 政策催化 + 风险清单

---

## Phase 2：可比公司分析（`a-share-comps-analysis`）

**触发条件：** 有明确目标标的，或 Phase 1 产出了候选列表。

**输入：** 目标公司代码/名称 + 可比公司列表（可不提供，自动筛选）
**输出：** `./out/comps_analysis.xlsx`

**执行步骤：**

1. 加载 `a-share-comps-analysis` skill
2. 通过 `dfcf-finance-tool` 拉取经营 + 估值数据
3. 用 `openpyxl` 构建 Excel 分析表
4. 提炼 PPT 所需关键结论：
   - 目标公司 PE/PB/ROE vs 中位数
   - 溢价/折价驱动因素
   - 异常值说明

### 数据获取的坑与回退策略

**dfcf `data()` 对可比公司可能静默返回 0 tables。** 目标公司（五粮液 000858）查询正常，但同样的 query 格式对蓝色光标、省广集团等返回 `dataTableDTOList: []`。这不是 API 挂了——是东方财富的 query 解析对非目标公司失效。

**回退策略（按优先级）：**

| 优先级 | 方法 | 适用场景 |
|--------|------|----------|
| 1 | `data()` 逐只查 | 目标公司优先，大概率成功 |
| 2 | `web_search()` | dfcf 返回空时，搜市值/营收/毛利率等公开数据 |
| 3 | `web_extract()` | 深度页面（财报解读、招股书摘要）提取结构化数据 |

**实战验证过的搜索 query 模式：**
```
"省广集团 002400 华扬联众 603825 市值 股价 2026年5月"
"蓝色光标 300058 AI营销 IPO 毛利率 2025"
```

**注意：** web_search 拿到的数据是近似值。在 Excel 的备注列标注"估算"或"近似值"，并在免责声明中说明。`screen()` 对行业关键词也会失败（返回 `参数校验失败`），不要依赖它拉可比列表——用手动列举 or web_search 同业名单。

---

## Phase 3：研报 PPT 组装（`powerpoint`）

**输入：** Phase 1 的 Markdown + Phase 2 的 Excel 数据
**输出：** `./out/research_report.pptx`

### 两种生成策略

| 策略 | 适用场景 | 文件结构 |
|------|----------|----------|
| **单文件**（推荐） | 8-12页标准研报，数据已齐全 | 一个 `build_pptx.js`，内含所有 slide 定义 |
| **多文件** | 大型项目、多人协作 | `slides/slide-NN.js` + `compile.js` |

**单文件模式已验证可行**（本次利欧研报即用此模式）。优势：无跨文件引用问题，`require('pptxgenjs')` 只一次，compile 一步到位。

**模板：** `templates/research-report-pptx.js` — 9页标准结构（Cover→结论），填充 DATA PLACEHOLDER 即可使用。

```bash
cd ~/out/slides && mkdir -p output
NODE_PATH=$(npm root -g) node build_pptx.js
```

### openpyxl 在 Hermes venv 中的注意事项

Hermes 的 `terminal()` 使用自身 venv 的 Python（`~/.hermes/hermes-agent/venv/bin/python3`），
而 `pip install openpyxl --break-system-packages` 可能装到用户 site-packages。
运行时如果报 `ModuleNotFoundError`，用：

```bash
PYTHONPATH=$HOME/.local/lib/python3.12/site-packages python3 script.py
```

### 推荐 PPT 结构（8-12 页）

| 页 | 类型 | 内容 | 数据来源 |
|----|------|------|----------|
| 1 | Cover | 行业/标题 + 日期 + 分析师声明 | — |
| 2 | TOC | 报告目录（3-5 章节） | — |
| 3 | Sector Overview | 行业规模、增速、产业链图谱 | Phase 1 |
| 4 | Competitive Landscape | CR5 龙头对比表、竞争格局图 | Phase 1 |
| 5 | A-Share Factors | 政策、北向资金、融资情绪 | Phase 1 |
| 6 | Valuation Context | PE/PB 当前 vs 历史分位 | Phase 1 |
| 7 | Section Divider | "可比公司分析" | — |
| 8 | Operating Metrics | 营收/增长/利润率对比 | Phase 2 |
| 9 | Valuation Comps | PE/PB/PS 对标柱状图 | Phase 2 |
| 10 | Statistics | 统计分布（中位数/分位数） | Phase 2 |
| 11 | Investment Implications | 机会 + 风险 + 实战清单 | Phase 1+2 |
| 12 | Disclaimer | 免责声明 + 分析师联系方式 | — |

### 配色与风格

- 使用 `powerpoint` skill → `references/design-system.md` 选配色
- 推荐：**Pure Tech Blue (#15)** 或 **Business & Authority (#2)** 为金融研报风格
- 字体：微软雅黑（中文）+ Arial（数字）
- 风格：Soft / Sharp — 根据受众（内部 Sharp，客户 Soft）

### 图表嵌入

方法：先用 Python/Excel 生成图表 PNG → 嵌入 PPT 对应页。

```python
import openpyxl
import matplotlib.pyplot as plt

# 从 comps_analysis.xlsx 读取数据 → 用 matplotlib 生成估值对比柱状图
# 输出 PNG → PPT 用 addImage 嵌入
```

---

## 一键启动接口

用户最短输入：

> "分析半导体设计板块，对标韦尔股份"

系统自动：
1. 激活 `a-share-sector-overview` → 出行业分析
2. 激活 `a-share-comps-analysis` → 出可比分析
3. （如涉及个股估值判断）激活 `a-share-valuation-report` → 出深度估值报告
4. 激活 `powerpoint` → 出研报 PPT
5. 全部输出到 `./out/` 目录

---

## 输出物清单

```
./out/
├── sector_analysis.md          # 行业深度 Markdown
├── comps_analysis.xlsx         # 可比分析 Excel（含公式）
├── valuation_report.md         # 个股深度估值报告（Phase 3b 可选）
├── research_report.pptx        # 研报 PPT
└── charts/                     # 图表 PNG（如有）
    ├── pe_comparison.png
    └── rev_growth.png
```

---

## Phase 5：飞书交付（可选）

产出 Markdown 研报后，直接推送到飞书：

```bash
cd ~ && lark-cli docs +create --doc-format markdown \
  --content '@Fugui-research-lab/research/报告名.md' \
  --format json
```

详见 → `references/feishu-delivery.md`

---

## 多股并行研究（`delegate_task` 模式）⭐

当用户要求分析 2-3 只股票时，用 `delegate_task` 并行跑（已验证：2 只约 5 分钟完成）：

```python
tasks: [
  {
    goal: "为XXX生成深度投研报告，覆盖叙事/护城河/估值/基本面/技术面。用妙想DFCF获取数据+web_search补充。输出Markdown到 ~/Fugui-research-lab/research/。",
    context: "股票代码、用户持仓成本、已知叙事逻辑、催化剂事件...",
    toolsets: ["terminal", "web", "file"]
  },
  {
    goal: "同上格式，为YYY生成...",
    context: "...",
    toolsets: ["terminal", "web", "file"]
  }
]
```

### 个股深度研报标准结构（五维分析）

每只股票的 subagent 必须按以下 5 节输出：

| 章节 | 内容 | 数据来源 |
|------|------|----------|
| 一、叙事(Narrative) | 公司的故事/市场定价/催化剂/为什么现在值得关注 | web_search + 妙想 |
| 二、护城河(Moat) | 技术壁垒/客户粘性/规模优势/转换成本 + 评分表 | 妙想财务 + web_search |
| 三、估值(Valuation) | PE/PB/PS当前水位 vs 历史分位 vs 同行对比 + 情景分析 | 妙想 data() 逐只查 + screen/web_search 可比组 |
| 四、基本面(Fundamentals) | 营收/利润/毛利率趋势/ROE/业务线拆解/现金流/风险 | 妙想财务数据 |
| 五、技术面(Technicals) | MACD/KDJ/RSI/BOLL/均线 + 关键支撑压力位 + 操作建议 | 妙想技术指标 |

每只股票的 subagent 独立完成：妙想数据采集→web_search 行业补充→按五维结构写 Markdown→`write_file` 到 `~/Fugui-research-lab/research/`。主 agent 只做收尾（飞书推送/总结/Git 提交）。

### 🔒 隐私规则（强制）

**所有深度研报属于个人投资判断，不得上传到公开 GitHub。** 本地保存在 `~/Fugui-research-lab/research/`（私有仓库，无 remote）。推送研报到飞书后，无需同步到 GitHub——已配置 `research/` 整目录在 `.gitignore` 中排除。

### 飞书交付

```bash
# 创建新文档
cd ~ && lark-cli docs +create --doc-format markdown \
  --content '@Fugui-research-lab/research/报告名.md' --format json

# 更新已有文档（全量覆盖）
cd ~ && lark-cli docs +update --doc <doc_token或URL> \
  --command overwrite --doc-format markdown \
  --content '@Fugui-research-lab/research/报告名.md' --format json
```

**注意**：`+update` 的 doc token 通过 `--doc` 标志传递（不是位置参数）。`--content` 支持 `@file` 相对路径（只接受 cwd 下的相对路径，不支持绝对路径）。

---

## 局限性声明

每份报告必须包含：

> **分析师声明：** 本报告基于公开数据自动生成（数据源：东方财富），不构成投资建议。估值对标仅反映当前市场定价，不预测未来走势。行业分析中的判断为基于数据的推演，不代表确定性结论。投资有风险，决策须谨慎。

---

## 依赖

- `a-share-sector-overview` skill
- `a-share-comps-analysis` skill
- `powerpoint` skill
- `dfcf-finance-tool` skill
- Python：`openpyxl`、`matplotlib`（图表）、`markitdown`（文本提取）

---

## 与 Anthropic pitch-deck 的对应关系

| Anthropic | 我们的 |
|-----------|--------|
| Pitch Agent（comps→pitch deck） | `a-share-research-report` 管道 |
| `comps-analysis` skill | `a-share-comps-analysis` |
| `sector-overview` skill | `a-share-sector-overview` |
| `pptx-author` (python-pptx) | `powerpoint` (PptxGenJS) |
| `pitch-deck` (模板填充) | PPT Phase 3（从数据组装） |
| S&P/FactSet MCP | 东方财富 API |

## 外部技能适配方法论

**Read [references/external-skill-adaptation.md](references/external-skill-adaptation.md)** for the adaptation checklist used to convert Western financial skills to A-share versions. Covers data source substitution, market convention remapping, and A-share-specific dimension layering. Use this when adapting additional skills from `anthropics/financial-services` or similar repos.
