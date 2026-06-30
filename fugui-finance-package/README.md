# 代码包 — 详见根目录 SKILL.md

王富贵的 A 股投资分析工具箱。**脚本能做的不用 skill，skill 能做的不用 LLM。**

## 目录

| 模块 | 定位 | 核心文件 |
|------|------|---------|
| **dfcf_finance** | 东方财富数据引擎 + 分析层 | `dfcf_finance.py` (v3.0, 531行) |
| **spring-river-warm** | 个股深度估值引擎 | `valuation_rules.py` + `clean_financials.py` |
| *peer-comps-builder* | 可比公司对标 | *(待迁移)* |
| *sector-deep-dive* | 行业深度分析 | *(待迁移)* |
| *research-pipeline* | 研报自动生成管道 | *(待迁移)* |

## 设计理念

- **分层降级**：脚本 → skill 框架 → LLM。能代码算的不让 LLM 猜
- **白盒优先**：prompt 模板可见，数据来源可追溯
- **实战导向**：TTM PE 而非动态 PE，周期股不用 PE 顶部估值
- **轻量独立**：每个模块独立可运行，不依赖框架

## 版本

- **dfcf_finance v3.0** (2026-05-30) — 分析层：个股诊断/财报解读/宏观/行业/公司深度
- **spring-river-warm v1.0** (2026-06-01) — 合并 enlightened-me-money + a-share-valuation-report

## 环境依赖

```bash
pip install requests openpyxl
```

东方财富数据需 `MX_APIKEY` 环境变量。
