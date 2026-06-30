# Fugui Research Lab — 技能索引

> 更新：2026-06-30 | 维护：华生 (Watson)

本索引覆盖 Hermes 中所有与投研、数据、可视化相关的技能。每个技能标注了触发词、输入输出、以及底层代码/数据路径。

---

## 一、核心投研管道（7 个技能）

### 1. dfcf-finance-tool — 东方财富数据工具

- **触发词**：查股价/行情/财报/资讯/选股/诊断
- **10 场景**：数据层 5 + 分析层 5
  - 数据：行情财务、资讯搜索、智能选股、自选股管理、筹码峰
  - 分析：个股诊断、财报解读、宏观研究、行业分析、公司深度
- **底层代码**：`fugui-finance-package/dfcf_finance/dfcf_finance.py`
- **类名**：`DFCFFinance`（不是 DFCF）
- **关键方法**：`data()` / `kdj()` / `macd()` / `news()` / `screen()` / `diagnosis()`

### 2. a-share-sector-overview — 行业深度分析

- **触发词**：分析XX行业/XX板块/行业深度/TAM/竞争格局
- **输出**：`sector_analysis.md`（行业规模、增速、CR5、估值水位、政策催化）
- **联动**：输出给 `a-share-comps-analysis` 和 `a-share-research-report`

### 3. a-share-comps-analysis — 可比公司分析

- **触发词**：估值对比/同行对比/可比估值/对标分析
- **输出**：`comps_analysis.xlsx`（经营指标+估值倍数+统计分布）
- **回退策略**：DFCF data() 静默失败 → web_search → web_extract

### 4. a-share-research-report — 研报自动生成管道

- **触发词**：出一份研报/写个行业深度/分析XX股票
- **管道**：sector-overview → comps-analysis → PPT
- **输出**：Markdown + Excel + PPT（标准 8-12 页）
- **今天刚跑的案例**：格力电器 + 深科技 双深度研报

### 5. a-share-technical-backtest — 技术指标回测引擎

- **触发词**：布林带回测/KDJ回测/MACD回测/策略回测
- **支持指标**：布林带、KDJ、MACD、组合信号
- **输出**：模拟交易记录 + 绩效归因（夏普比率、最大回撤、胜率）

### 6. horizontal-vertical-deep-research — 横纵分析深度研究

- **触发词**：深度研究/横纵分析/发展史+竞品/帮我研究一下XX
- **方法**：纵向（发展史叙事）+ 横向（竞品切片）+ 交汇判断
- **分类型**：产品/公司/技术概念/人物，自动适配分析维度
- **输出**：1-3 万字可读性强的深度报告

### 7. lucky-bamboo — 富贵竹投资分析总入口

- **触发词**：股票/投资/回测/估值/富贵竹
- **定位**：所有投资分析技能的聚合入口
- **子技能覆盖**：数据获取、技术回测、估值分析、行业研究、研报生成

---

## 二、辅助工具（4 个技能）

### 8. company-name-abbreviation — 公司全称→简称映射

- **触发词**：公司简称/客户标识/报表透视表/VLOOKUP
- **规则**：去地域前缀 + 去公司后缀 → 保留核心商号
- **用途**：报表透视表、VLOOKUP、客户标识标准化

### 9. darwin-skill — 达尔文进化器

- **触发词**：进化/优化提示词/变异/自然选择
- **用途**：用进化算法自动优化 prompt/regex/SQL/交易策略参数
- **输入**：候选种子 + 适应度函数 → 输出最优个体

### 10. personal-data-lab — 个人数据实验室

- **触发词**：数据追踪/健康数据/财务追踪/搭建数据档案
- **结构**：14 目录 + CSV 每指标一文件 + 头部强制注释
- **迁移状态**：health→fugui-life-health, finance→fugui-life-finance
- **下一步**：Polyrepo（Fugui/Health/Finance/Writing/Office/Research/Tools/Shared/）

### 11. course-production-pipeline — 课件生产（参赛版/自用版）

- **触发词**：做课/课件/参赛/PPT/分镜/WorkBuddy/一看二拆三封
- **五步法**：写分镜 → 列生图清单 → 模板逆向 → WorkBuddy组装 → 人工补完
- **核心版式**：#19（封面） / #12（章扉） / #17（万能内页） / #16（左图右文）
- **结构**：32 页参赛版，一看二拆三封，只解决一个痛点

---

## 三、工具恢复与开发（3 个技能）

这些是基础设施维护技能，投研日常不常用，但工具坏了时需要：

| 技能 | 用途 |
|------|------|
| `hermes-tool-recovery-workflow` | 从历史会话恢复丢失的 Hermes 工具函数 |
| `hermes-tool-file-recovery-and-repair` | 修复损坏的工具文件 |
| `create-financial-tool-development-report` | 生成金融工具开发报告（功能/架构/测试/问题） |

---

## 四、目录结构

```
~/Fugui-research-lab/
├── fugui-finance-package/          # 核心代码
│   ├── dfcf_finance/               # DFCF 数据工具 (DFCFFinance 类)
│   └── spring-river-warm/          # 春江水暖
├── lucky-bamboo/                   # 富贵竹
│   ├── scripts/                    # quick_scan v2.9, fallback_scan
│   ├── references/                 # 参考数据
│   └── observation-log/            # 观察日志
├── research/                       # 🔒 研报输出（私有）
├── course-dev/                     # 🔒 课件开发（私有）
├── docs/                           # 文档（当前文件所在位置）
│   ├── SKILLS-INDEX.md             # 本文件
│   ├── workflows/                  # 各技能的工作流说明
│   ├── methods/                    # 方法论
│   └── notes/                      # 研究笔记
└── site/                           # MkDocs 站点
```

---

## 五、妙想 DFCF 快速调用

```bash
cd ~/Fugui-research-lab

# 查行情
python3 -c "
import sys; sys.path.insert(0, 'fugui-finance-package')
from dfcf_finance.dfcf_finance import DFCFFinance
d = DFCFFinance()
print(d.data('000002'))
"

# 查 KDJ
python3 -c "
import sys; sys.path.insert(0, 'fugui-finance-package')
from dfcf_finance.dfcf_finance import DFCFFinance
d = DFCFFinance()
print(d.kdj('000002', n=14, m1=3, m2=3))
"
```

---

## 六、技能联动地图

```
用户输入（股票/行业/问题）
        │
        ├─ 快速行情/数据 → dfcf-finance-tool
        │
        ├─ 行业深度分析 → a-share-sector-overview
        │       └─ 输出给 → a-share-comps-analysis
        │               └─ 输出给 → a-share-research-report
        │                       └─ 组装 PPT → course-production-pipeline
        │
        ├─ 技术回测 → a-share-technical-backtest
        │
        ├─ 深度研究（叙事/护城河/估值/基本面/技术面）
        │   └─ horizontal-vertical-deep-research
        │
        └─ 参数优化 → darwin-skill
```

---

> **维护规则**：新增或修改技能后，更新本文件。代码、技能文件、文档索引三处保持一致。
