# enlightened-me-money v1 — 个股深度估值框架

不是财务指标复读机，是有方法论的估值引擎。

## 管线

```
数据采集 → 数据清洗 → 推理规则 → Regime 分类 → 多方法估值 → 预期差 → 投资语言
```

## 核心脚本

| 文件 | 功能 |
|------|------|
| `clean_financials.py` | 东方财富混杂格式 → float，自动计算 QoQ/YoY/TTM |
| `valuation_rules.py` | 利润质量/成长质量/估值驱动检测 + Regime 自动分类 |

## Regime 分类

```python
from valuation_rules import RuleEngine

regime = RuleEngine.classify_regime(
    gm_volatility=0.42,   # 近3年毛利率极差
    revenue_growth=0.80,  # 近3年营收CAGR
    roe=0.15,
)
# → CYCLE / GROWTH / STEADY
```

自动匹配估值方法：周期股用 PB，高成长用 PS+Forward PE，白马用 DCF+ROIC。

## 推理规则

- 利润质量：CFO/净利润 < 0.8 → 偏弱
- 应收异常：应收增速 > 营收增速 +20pct → 渠道压货风险
- 成长质量：营收+40% 但毛利率-5pct → 低价扩张
- 估值驱动：PE↑ + EPS↓ → 纯估值扩张（非业绩驱动）

## 版本

v1 (2026-04) — 单 agent 管线。v2 多 agent 规划中。
