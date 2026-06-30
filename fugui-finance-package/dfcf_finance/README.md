# dfcf_finance v3.0 — 东方财富金融工具

OOP + 自动路由 + 白盒 prompt。10 个场景一个类搞定。

## 架构

| 层 | 方法 | 说明 |
|---|------|------|
| **数据层** | `data(query)` | 行情/财务指标 |
| | `news(query)` | 资讯/公告/研报 |
| | `screen(query)` | 自然语言选股 |
| | `watchlist_get()` / `watchlist_manage()` | 自选股管理 |
| **分析层** | `stock_diagnosis(stock)` | 综合诊断 |
| | `financial_report(stock)` | 财报同比环比解读 |
| | `macro_research(topic)` | 宏观政策研究 |
| | `industry_analysis(industry)` | 行业全景分析 |
| | `company_deep_dive(stock)` | 公司基本面深度 |

每个分析层方法返回结构化 prompt 模板 + 原始数据，由 LLM 生成最终报告。

## 自动路由

```python
tool.route("平安银行最新股价")        # → data()
tool.route("平安银行诊断")            # → stock_diagnosis()
tool.route("半导体行业分析")          # → industry_analysis()
```

## 环境要求

- Python 3.9+
- `MX_APIKEY` 环境变量
- 依赖：`requests`

## 版本

v3.0 (2026-05-30) — 分析层上线，新增 5 个分析场景

详见 `references/` 下的 API 结构、时间序列数据、估值指标、AI 供应链框架等参考文档。
