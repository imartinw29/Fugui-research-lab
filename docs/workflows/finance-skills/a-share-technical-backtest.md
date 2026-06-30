---
name: a-share-technical-backtest
description: "A股技术指标策略回测引擎 — 布林带/KDJ/MACD多指标组合信号，模拟交易，绩效归因。"
version: 1.0.0
author: 华生 @ Hermes
license: MIT
---

# A股技术指标策略回测

从用户交易观察到可验证结论的完整管道：**拉数据 → 算指标 → 找信号 → 模拟交易 → 输出绩效**。

## 触发条件

- "回测这策略" / "帮我验证这个买入逻辑"
- 用户描述了基于K线/布林带/KDJ/MACD的规则
- "从XX日期到现在，看看哪些信号准"

## 数据源

| 数据源 | API | 说明 |
|--------|-----|------|
| **腾讯**（首选） | `web.ifzq.gtimg.cn/appstock/app/fqkline/get` | 稳定、无需key、前复权 |
| 东方财富 push2his | `push2his.eastmoney.com` | 偶尔拒连，备选 |
| 东方财富 dfcf skill | `dfcf_finance.py` data() | 仅实时数据，无历史K线 |

**代码映射：**
- 科创板 688xxx → `sh688xxx`
- 创业板 301xxx → `sz301xxx`  
- 主板/中小板 002xxx/600xxx → `sz002xxx` / `sh600xxx`

**拉300条日线足够（~1年+）。** 腾讯API返回 `"qfqday"` key，字段：`[日期, 开, 收, 高, 低, 成交量]`。

坑：`execute_code` 沙箱网络受限，回测脚本用 `terminal()` 运行，别用 `execute_code`。

## 指标计算（pandas-free，纯 math+stdlib）

脚本模板见 `scripts/backtest_engine.py`。

### 布林带 BOLL-M(20)
```python
# 20日均线 ± 2σ
w = closes[i-19:i+1]
ma = sum(w) / 20
std = math.sqrt(sum((x-ma)**2 for x in w) / 20)
bb_up = ma + 2*std
bb_down = ma - 2*std
```

### KDJ(14,3,3) — 用户自定参数，不是默认9
```python
period = 14
hh = max(highs[i-13:i+1]); ll = min(lows[i-13:i+1])
rsv = (close - ll) / (hh - ll) * 100  # hh==ll时取50
K = 2/3 * prev_K + 1/3 * rsv
D = 2/3 * prev_D + 1/3 * K
J = 3*K - 2*D
```

### MACD(12,26,9)
```python
EMA12[i] = EMA12[i-1] * 11/13 + close[i] * 2/13
EMA26[i] = EMA26[i-1] * 25/27 + close[i] * 2/27
DIF = EMA12 - EMA26
DEA[i] = DEA[i-1] * 8/10 + DIF[i] * 2/10
BAR = 2 * (DIF - DEA)
```

## 交易模拟规则

**不重复持仓**：已有仓位时忽略新买入信号，直到卖出后再开新仓。

```python
if not holding and buy_signal:
    enter_position()
elif holding and sell_signal:
    close_position()
```

**期末强制平仓**：回测结束时若仍持仓，以最后收盘价平仓并标记「持仓中」。

## 输出格式

每只股票输出：
1. **逐笔交易表**：买入日/价 → 卖出日/价 → 收益率 → 持仓天数 → 买入时BB位置
2. **汇总**：笔数、胜率、累计收益、平均/最佳/最差、vs买入持有
3. **当前状态**：最新收盘、BB位置%、KDJ/MACD值、是否触发买入信号

全部股票输出：
4. **信号规律分析**：所有买入信号的BB位置/K值/J值分布

## 已知规律（从此session回测中提炼）

| 维度 | 好信号特征 | 危险信号 |
|------|-----------|---------|
| BB位置 | **10-25%**（中下轨之间） | <5%（恐慌破位）或>30%（不够低） |
| K值 | **10-18** | <8（太弱连续阴跌）或>20（位置偏高） |
| J值 | **-5 ~ +10** | <-10（加速恐慌）或>15（反弹已走完） |
| MACD | 绿柱**连续收窄**（bar > 前一日） | 绿柱还在加速放大 |

### 关键陷阱

1. **信号连发**：同一买点可能连续触发多日信号。不必第一天冲进去，第2-3天确认更稳。
2. **布林带+KDJ先到位，MACD最后确认**：K线已在低位+KDJ超卖，但MACD绿柱还在放大 → 不买，等拐头。
3. **必须有止损**：不是所有买入信号都能等来卖出信号（如利欧5/6→6/2亏16%）。建议买入后跌5-8%强制平仓。
4. **牛市跑输买入持有**：在大趋势行情中（此session的佰维+178%、江波龙+175%），震荡策略天然跑输。策略优势在震荡市。

## 优化方向（用户后续可探索）

- KDJ阈值从K<30收紧到K<20
- 信号连发时分批建仓（分2-3天）
- 上轨卖出改为"突破上轨后持有直到回落到上轨以下"
- 加入止损规则回测（-5%、-8%、-10%）
- 扩展到60分钟/30分钟级别

## 快速诊断: KDJ 超买扫描

当用户问"J值是不是太高了"时，用 `scripts/kdj_overbought_scan.py` 快速回答：

```bash
python3 scripts/kdj_overbought_scan.py sh000002
```

输出近15日KDJ表 + 历史J>100时段 + 前向收益 + 上下文解读。比完整回测快100倍，适合聊天中的即时诊断。

## 回测脚本

→ `scripts/backtest_engine.py` — 可直接运行的完整回测脚本，修改 `stocks` 列表和策略参数即可复现。

## 历史分析记录

→ `references/session_20260602_findings.md` — 佰维/澜起/江波龙/利欧四股2025.10-2026.06回测结果与模式发现。

## pip 安装坑

WSL环境下 `pip install pymupdf` 可能超时。使用清华镜像：
```bash
pip3 install pymupdf -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages
```
