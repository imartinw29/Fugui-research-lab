# Fugui Finance Package 🥜

王富贵的 A 股投资分析工具箱。数据驱动，逻辑白盒，不做黑盒算命。

## 目录

| 模块 | 定位 | 核心文件 |
|------|------|---------|
| **dfcf_finance** | 东方财富数据引擎 + 分析层 | `dfcf_finance.py` (v3.0) |
| **enlightened-me-money** | 个股深度估值框架 | `valuation_rules.py` + `clean_financials.py` |
| *a-share-comps-analysis* | 可比公司对标 | *(待迁移)* |
| *a-share-valuation-report* | 个股估值报告生成 | *(待迁移)* |
| *a-share-sector-overview* | 行业深度分析 | *(待迁移)* |
| *a-share-research-report* | 研报自动生成 | *(待迁移)* |

## 设计理念

- **白盒优先**：prompt 模板可见，数据来源可追溯，不信任任何黑盒 API
- **实战导向**：工具服务于决策，不是服务于演示。指标选 TTM PE 而非动态 PE
- **轻量独立**：每个模块一个 `.py` 文件，不依赖框架，Hermes/nanobot/独立脚本通用

## 使用方式

```python
# 数据层
from dfcf_finance import DFCFFinance
tool = DFCFFinance(api_key="your_key")
result = tool.data("佰维存储 最新价 PE(TTM)")

# 分析层
result = tool.stock_diagnosis("佰维存储")
result = tool.industry_analysis("存储芯片")

# 估值引擎
from valuation_rules import RuleEngine
regime = RuleEngine.classify_regime(gm_volatility=0.42, revenue_growth=0.80, roe=0.15)
```

## 版本

- **dfcf_finance v3.0** (2026-05-30) — 新增分析层：个股诊断/财报解读/宏观研究/行业分析/公司深度
- **enlightened-me-money v1** (2026-04) — 估值推理规则引擎 + 数据清洗

## 环境依赖

```bash
pip install requests
```

东方财富数据需 `MX_APIKEY` 环境变量（从东方财富妙想 Skills 页面获取）。
