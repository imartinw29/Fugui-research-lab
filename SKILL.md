# 投研技能系统

> 方法论层——只描述流程和能力，不描述"我验证过什么"。

## 能力矩阵

| 能力 | 触发方式 | 描述 |
|------|---------|------|
| 数据获取 | `data()` | 东方财富API：行情/财报/选股/筹码峰 |
| 行业分析 | sector-overview | 市场规模、竞争格局、估值水位、政策催化 |
| 可比估值 | comps-analysis | 同业对标：经营指标+估值倍数+统计分布 |
| 研报生成 | research-report | 管道：行业分析→可比估值→PPT |
| 技术回测 | technical-backtest | 布林带/KDJ/MACD组合信号，模拟交易+绩效归因 |
| 深度研究 | deep-research | 横纵分析法：纵向发展史+横向竞品+交汇判断 |
| 策略进化 | darwin-evolver | 进化算法优化prompt/参数/策略 |

## 目录职责

| 目录 | 职责 | 公开 |
|------|------|------|
| `prompt/` | 各场景系统提示词 | ✅ |
| `scripts/` | 可执行Python代码 | ✅ |
| `templates/` | 报告模板 | ✅ |
| `examples/` | 脱敏案例（中性代码） | ✅ |
| `observations/` | 方法论规律记录（无股票名） | ✅ |
| `experiments/` | 策略实验与版本 | ✅ |
| `fugui-finance-package/` | 数据引擎+估值引擎 | ✅ |
| `lucky-bamboo/` | 策略脚本 | ✅ |
| `private/` | 自选池/持仓/回测/配置 | ❌ |
| `research/` | 深度研报 | ❌ |
| `course-dev/` | 课件 | ❌ |
| `data/` | 本地缓存 | ❌ |
