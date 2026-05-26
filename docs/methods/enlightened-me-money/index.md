---
name: enlightened-me-money
description: 个股深度估值报告框架 v1 — 数据清洗 → 推理规则 → regime分类 → 多方法估值 → 预期差 → 投资语言。含估值推理规则引擎(valuation_rules.py)和数据标准化(clean_financials.py)。v1单agent，v2/v3规划见底部roadmap。
category: finance
---

# 个股深度估值报告（Enlightened Me Money）v1

> **核心定位：有研究方法论的 Agent，不是财务指标复读机。**
> 与 `a-share-comps-analysis`（横向对标）互补，本 skill 做纵向深度估值。

## 触发条件

用户提到以下模式时激活：
- "用估值模板分析 XX"
- "按 enlightened-me-money 跑一下 XX"
- "个股深度估值 XX"

## 架构（单 Agent v1）

```
Step 0: 数据采集（delegate_task 并行：财务 / 行业 / 筹码）
Step 1: 数据清洗 → clean_financials.py → Canonical Schema
Step 2: 推理规则 → valuation_rules.py → 利润质量/成长质量/估值驱动
Step 3: Regime 分类 → 周期/成长/白马 → 匹配估值方法
Step 4: 多方法估值 → PE/PS/DCF/分部（按 regime 选择）
Step 5: 预期差分析 + 可信度评分
Step 6: 投资语言输出 + 观测阈值
```

## Step 0：数据采集清单

### 必拉数据

**A. 财务时间序列（至少 8 季度）**
```
营收 / 归母净利 / 扣非净利 / 毛利率 / 净利率
ROE / ROIC / 资产负债率
经营现金流(每股) / 存货 / 应收账款 / 合同负债 / 资本开支
```
→ 计算：QoQ / YoY / TTM / 毛利率变化趋势

**B. 行业相对指标**
```
行业平均 PE / ROE / 毛利率 / 营收增速 / PS
```
→ 从东方财富板块数据或 web_search 获取

**C. 筹码结构时间序列**
```
北向持股及30日变化 / 融资余额 / 机构持仓 / 解禁日程
```

## Step 1：数据清洗

使用 `scripts/clean_financials.py`：
- `parse_dfcf_value()` 将东方财富混杂格式("68.14亿元"/"42.22%"/"-5.748元") → float
- `compute_derived()` 自动计算 QoQ / YoY / TTM / 毛利率变化 / 存货周转
- 所有原始数据保留，不做分析

## Step 2：推理规则引擎

使用 `scripts/valuation_rules.py`，关键规则：

| 规则 | 触发条件 | 结论 |
|------|---------|------|
| 利润质量 | CFO/净利润 < 0.8 | 利润质量偏弱 |
| 应收异常 | 应收增速 > 营收增速 +20pct | 渠道压货风险 |
| 成长质量 | 营收+40% 且毛利率-5pct | 依赖低价扩张 |
| 存货积压 | 存货增速 >> 营收增速 | 减值风险 |
| 估值驱动 | PE↑ + EPS↓ → 纯估值扩张 | PE↑ + EPS↑ → 业绩驱动 |

**所有规则输出可审计——不是 prompt 硬写，是 Python 函数返回。**

## Step 3：Regime 分类

```python
from valuation_rules import RuleEngine, Regime

regime = RuleEngine.classify_regime(
    gm_volatility=近3年毛利率极差,  # 如 0.42
    revenue_growth=近3年营收CAGR,   # 如 0.80
    roe=当前ROE,
)
# → Regime.CYCLE / GROWTH / STEADY / UNCLASSIFIED
```

根据 regime 自动匹配估值方法：

| Regime | 主方法 | 避免 |
|--------|-------|------|
| 周期股 | PB + 库存周期位置 | PE（顶部利润最大=PE最低，具误导性） |
| 高景气成长 | PS + Forward PE | DCF（假设过于敏感） |
| 稳定白马 | DCF + ROIC | PS（成熟期不适用） |

## Step 4-6：完整框架结构

```
1、公司概况与业务结构
   ├ 业务拆解表
   ├ 行业周期位置
   └ 竞争优劣势

2、核心业务表现与增长逻辑

3、最新财报数据解读
   ├ 核心财务指标表
   ├ 盈利能力 + 运营能力 + 偿债能力
   ├ 资本回报与现金流（ROE拆解/ROIC/FCF 剪刀差）
   ├ 推理规则检查结果（利润质量/成长质量/应收异常/存货积压）
   └ 研发投入

4、估值
   4.1 隐含PE校验与市场定价拆解
       ├ 动态PE vs TTM PE（必须同时报告，解释差异）
       └ 历史PE Band
   4.2 可比公司估值锚定
       └ 筹码结构（北向/融资/机构）+ 解禁压力
   4.3 Regime 分类 + 方法选择
       └ 输出：公司属于___regime，主用___方法，不用___
   4.4 前瞻估值法（乐观/中性/悲观）
       ├ 远期PE法
       ├ PS辅助法
       └ 分部估值法（触发：毛利率差>15pct 或 增速差>20pct）
   4.5 估值自洽性校验
       ├ 多方法交叉
       ├ DCF隐含增速反推（FCF为正才启用）
       └ 估值驱动来源（调用 check_valuation_driver）
   4.6 预期差分析 ← 新增
       ├ 市场当前定价隐含假设
       ├ 公司实际经营数据
       └ 潜在超预期 / 低于预期点
   4.7 市场在押注什么

5、风险提示

6、估值结论
   ├ 估值可信度评分（高/中/低）
   ├ 核心估值区间
   ├ 【投资语言】市场押注___，核心变量___，若___不达预期则估值坍塌到___ ← 强制输出
   ├ 催化剂时间线
   └ 观测指标与阈值（持有/减仓/离场）
```

## 投资语言（强制输出格式）

估值结论必须包含此模块，不得省略：

```
当前阶段：[周期中期/顶部/底部/成长早期/成熟期]
市场交易逻辑：[一句话]
核心矛盾：[一句话]
估值锚：[核心观测指标]
最重要观测指标：[一个]
什么时候估值会崩：[条件]
什么时候会二次扩张：[条件]
```

## 估值可信度评分

```
✅ 高确定：行业稳定 + 连续盈利 + 现金流健康 + 无单一客户依赖
⚠️ 中等：具备3/4
❌ 低确定：强周期/现金流为负/政策敏感/技术路线存疑
```

**评分本身就是估值结论的一部分。** 低确定标的的宽估值区间（如乐观+38%、悲观-64%）是信号，不是模型缺陷。

## 数据源优先级

1. 东方财富 API（`dfcf-finance-tool`）
2. 年报/招股书原文（巨潮资讯网 `web_extract`）— 分业务数据
3. `web_search` — 行业均值、可比公司回退
4. PE Band / 情绪数据 — v1 降级为文字定性，v2 cron job

## 依赖

- `dfcf-finance-tool` skill
- `scripts/valuation_rules.py` — 推理规则引擎
- `scripts/clean_financials.py` — 数据清洗
- `a-share-comps-analysis`（可选，4.2 节数据）

---

## v2 / v3 路线图

### v2（多 Agent）
- Data Agent：独立拉数据 + 清洗 + 衍生指标
- Business Agent：商业模式 / 竞争格局 / 增长来源
- Financial Agent：盈利质量 / 杠杆 / 运营效率
- Valuation Agent：PE/PS/DCF/SOTP + 预期差
- Risk Agent：政策 / 技术路线 / 客户集中 / 解禁
- IC Agent：裁决 → 多空汇总 + 核心矛盾 + 可信度

### v3（持续监控）
- `enlightened-me-money-evo` cron job：每日跑估值异动检测
  - PE percentile > 95%
  - 股价↑ + EPS↓ 背离
  - 北向 spike
  - 存货增速 >> 营收增速
  - Regime 切换检测（成长→周期杀估值）

## 局限性声明

每份报告必须包含：

> **分析师声明：** 本报告基于公开数据自动生成（数据源：东方财富），不构成投资建议。估值测算中的情景假设具有主观性，实际结果可能大幅偏离。投资有风险，决策须谨慎。
