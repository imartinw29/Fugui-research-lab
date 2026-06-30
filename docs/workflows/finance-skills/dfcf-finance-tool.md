---
name: dfcf-finance-tool
title: 东方财富金融工具
description: 10场景全覆盖(数据5+分析5) — 行情/资讯/选股/自选股/诊断/财报/宏观/行业/公司深度。统一接口 OOP 自动路由，代码托管 Fugui-research-lab/fugui-finance-package。
env:
  MX_APIKEY:
    description: 东方财富妙想 API Key（从东方财富妙想Skills页面获取）
    required: true
---

# dfcf-finance-tool 东方财富金融工具 v3.0

### 数据层

| 场景 | 方法 | 说明 |
|------|------|------|
| 行情/财务 | `data(query)` | 个股、板块、指数行情与财务指标（含筹码峰数据，见下方） |
| 资讯搜索 | `news(query)` | 新闻、公告、研报、政策 |
| 智能选股 | `screen(query)` | 自然语言条件筛选 |
| 自选股查询 | `watchlist_get()` | 获取已添加的自选股 |
| 自选股管理 | `watchlist_manage(action, stock)` | 添加/删除 |

#### 筹码峰（CYQ）查询（v2.4 新增 · 2026-06-16）

通过 `data()` 可拉取筹码分布数据：

```python
r = tool.data('000002 筹码分布 获利盘比例')
# 返回字段：
# 010000_CMPJCB = 平均持仓成本（元）
# 010000_HLP = 获利盘比例（%）
# 010000_CMFB_461_JZD70 = 70%筹码集中度（%）
# 010000_CMFB_461_JZD90 = 90%筹码集中度（%）
```

all-in-one query：`'000002 筹码分布 获利盘比例'` 一次查询返回全部四个指标。
| **分析层** | 个股诊断 | `stock_diagnosis(stock)` | 行情+财务+资讯 → 综合诊断 |
| | 财报解读 | `financial_report(stock)` | 最新财报同比环比分析 |
| | 宏观研究 | `macro_research(topic)` | 政策/数据/事件驱动研究 |
| | 行业分析 | `industry_analysis(industry)` | 选股+资讯+估值水温 |
| | 公司深度 | `company_deep_dive(stock)` | 基本面全景扫描+护城河分析 |

每个分析层方法返回结构化 prompt 模板 + 原始数据，由 LLM 生成最终分析报告。
比东方财富官方 Skills 的优势：透明（能看到完整 prompt）、灵活（可自定义模板）、统一（一个类搞定 10+ 场景）。

## 自动路由（增强版）

`route(query)` 自动判断场景：

**数据层：**
```
"贵州茅台最新股价"           → data()
"人工智能板块新闻"           → news()
"市盈率小于20的银行股"       → screen()
"查看我的自选股"             → watchlist_get()
"把宁德时代添加到自选股"     → watchlist_manage("add", "宁德时代")
```

**分析层（新增）：**
```
"平安银行诊断"               → stock_diagnosis()
"宁德时代财报解读"           → financial_report()
"半导体行业分析"             → industry_analysis()
"美联储加息对A股影响"        → macro_research()
"格力电器深度分析"           → company_deep_dive()
```

## 版本历史

### v3.2 (2026-06-25) — OHLC 五合一套餐 + data:null 补丁
- 🔥 **推翻旧文档**: 妙想支持完整 OHLC 五合一查询 (收盘+最高+最低+开盘+换手率), 字段码 326269/325898/326339/326386/326699 跨股票 100% 一致
- 🔧 **data:null 补丁**: `data()` 和 `news()` 内部仍残留 `.get("data",{})` 写法, 已改为 `raw.get("data") or {}`
- 新增 `references/miaoxiang-field-codes.md` — 字段码 + f-code 边缘票 + data:null 防护

### v3.1 (2026-06-24) — data(null) 崩溃修复 + 简报模板
- 🔧 **关键修复**：`raw.get("data", {})` → `raw.get("data") or {}`（data() 和 news() 两处）。当 API 返回 `data:null` 时，`.get("data", {})` 返回 None 而非 {}，导致 `AttributeError: 'NoneType' object has no attribute 'get'`。今日本 session 崩溃 3+ 次后修复。
- 新增 `references/morning-briefing-template.md` — 午盘/收盘简报查询模板（6步查询→5段输出）

### v3.0 (2026-05-30) — 分析层上线
- 新增 5 个分析场景：个股诊断、财报解读、宏观研究、行业分析、公司深度
- 每个分析场景返回结构化 prompt 模板 + 原始数据，由 LLM 生成最终报告
- 增强路由：自动识别分析类意图
- 辅助方法：`_extract_table_summary()`、`_extract_news_summary()`、`_extract_screen_summary()`
- 模拟组合接口保留但未启用（需额外授权）
- 新增 `references/morning-briefing-template.md` — 午盘/收盘简报模板，6步查询→5段输出结构
- 新增 `references/valuation_metrics.md` — PE/PB 解释 + TTM vs 动态 vs 静态口径
- 新增 `references/multi-stock-analysis-template.md` — 多股对比分析框架（公司画像→财务→行情→逻辑→结论→排名），含数据解读注意事项
- 新增 `references/ai_supply_chain_framework.md` — "耗材 > 铲子"投资框架 + MLCC/PCB 产业链
POST https://mkapi2.dfcfs.com/finskillshub/api/claw/query          # data
POST https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search    # news
POST https://mkapi2.dfcfs.com/finskillshub/api/claw/stock-screen    # screen
POST https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/get    # watchlist_get
POST https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/manage  # watchlist_manage
Header: apikey: {MX_APIKEY}
```

## 响应格式

```json
{
  "success": true,
  "data": { ... },
  "message": "查询成功",
  "timestamp": "2026-04-16T09:19:00Z"
}
```

- `success: true` = 业务成功（status==0 && success==True）
- `success: false` = 业务失败，外层 message 说明原因，data 包含原始返回

## Python 调用

```python
from dfcf_finance import DFCFFinance

tool = DFCFFinance()  # 读取 MX_APIKEY 环境变量
# 或：tool = DFCFFinance(api_key="your_key")

# 自动路由
result = tool.route("平安银行最新股价")

# 直接指定场景
result = tool.data("平安银行最新股价")
result = tool.news("存储芯片板块新闻")
result = tool.screen("市盈率小于30的科技股")
result = tool.watchlist_get()
result = tool.watchlist_manage("add", "宁德时代")
result = tool.watchlist_manage("delete", "比亚迪")
```

### 终端快速调用（Hermes 内一键）

```bash
cd ~/Fugui-research-lab && python3 -c "
import sys; sys.path.insert(0, 'fugui-finance-package')
from dfcf_finance.dfcf_finance import DFCFFinance
d = DFCFFinance()
r = d.data('000002 最新价 涨跌幅 成交额 主力净流入 换手率 开盘价 最高价 最低价')
print(r)
"
```
**注意：类名是 `DFCFFinance`，不是 `DFCF`。路径是 `fugui-finance-package/dfcf_finance/dfcf_finance.py`。**

## CLI 用法

```bash
python dfcf_finance.py 贵州茅台最新股价
python dfcf_finance.py 人工智能板块新闻
python dfcf_finance.py 市盈率小于20的银行股
```

## 已知坑

- **Agent 惯性偏误（三次纠正·2026-06-30）**：Agent 容易下意识先调用 web_search 再考虑妙想。凡是日级别及以上的行情查询，第一时间走妙想 data/news，不先 web_search。**触发规则：用户提股票、行情、KDJ/MACD/筹码峰等关键词→第一反应走终端调 DFCFFinance，不是 web_search。**
- **data:null 崩溃（v3.1已修复）**：raw.get("data", {}) 返回 None 导致崩溃，已改为 raw.get("data") or {}。
- **🔴 A/H股混淆（今日两次犯错 · 2026-06-24）**：蓝思(000651+06613)、澜起(000002+06809)等A+H股，妙想同时返回两个价格。A股带.SZ后缀，H股带.HK或「港」。取价必须优先.SZ，跳过.HK/港。今日误取蓝思H股26.58(实际A股52.28)，用户纠正。
- **data:null 崩溃（v3.1 已修复 · v3.2 补修残余 · 2026-06-25）**：`raw.get("data", {})` 当 API 返回 `data:null` 时返回 None。已全量改为 `raw.get("data") or {}`。`data()` 和 `news()` 两处均修复。
- **次新/边缘票组合查询返回 f-code（v3.2 新增）**：五合一 OHLC 查询对强达电路(301628)/源杰科技(688498)等返回 `f16/f15/f17/f8` 快照格式而非 `3xxxxx` 时间序列。调用方需检测格式不符时降级 push2his。详见 `references/ohlc-five-in-one.md`。
- `/query` 端点 **必须** 用 `toolQuery` 作参数名，不是 `query`；写错会返回 `{"error": "未知错误"}` 或 `114` 状态码
- nanobot 侧旧版 `mx_finance.py` 与 `dfcf_finance.py` 并存，只有 `dfcf_finance.py` 是 v2.1，旧文件已删除

## 跨平台同步规则

**Hermes 侧是主开发侧**。每次在 Hermes 上修复 bug 或升级版本后，必须同步：

### 1. GitHub（公开仓库）
```bash
# 主代码（Fugui-research-lab/fugui-finance-package）
cp ~/.hermes/skills/dfcf-finance-tool/scripts/dfcf_finance.py \
   ~/Fugui-research-lab/fugui-finance-package/dfcf_finance/

# references 同步
cp ~/.hermes/skills/dfcf-finance-tool/references/*.md \
   ~/Fugui-research-lab/fugui-finance-package/dfcf_finance/references/

# 提交
cd ~/Fugui-research-lab && git add fugui-finance-package/ && git commit && git push
```

### 2. nanobot（内网）
```bash
cp ~/.hermes/skills/dfcf-finance-tool/scripts/dfcf_finance.py \
   ~/.nanobot/workspace/skills/mx-finance/dfcf_finance.py
```

### 3. OpenClaw（备份副本）
```bash
cp ~/.hermes/skills/dfcf-finance-tool/scripts/dfcf_finance.py \
   ~/.openclaw/skills/eastmoney-dfcf-unified/scripts/dfcf_finance.py
```

## 相关模块

本 skill 是 fugui-finance-package 的数据引擎层。套装内其他模块：
- `spring-river-warm/` — 个股估值引擎（valuation_rules + clean_financials）
  - 外部 Peer Review → `references/spring_river_warm_peer_review.md`（股票喵，2026-06-01）
- `peer-comps-builder/` — 可比公司对标分析（待迁移）
- `sector-deep-dive/` — 行业深度分析（待迁移）
- `research-pipeline/` — 研报自动生成管道（待迁移）

源码：`github.com/imartinw29/Fugui-research-lab/tree/main/fugui-finance-package`（两边同步）

当 API 返回 `{"data": null}` 时，旧版 `raw.get("data", {})` 返回 `None`（字典默认值不生效），导致 `None.get("message")` 崩溃：

```python
# 错误版
inner = raw.get("data", {})        # data=null → inner=None
inner.get("message", "筛选失败")    # AttributeError: 'NoneType' object has no attribute 'get'

# 正确版
inner = raw.get("data") or {}       # data=null → inner={}
status = inner.get("status", raw.get("status", raw.get("code", -1)))  # fallback 到 raw 层
raw.get("message") or inner.get("message") or "筛选失败"  # 多层兜底
```

## Mock 测试注意

`patch.object(tool, "_call")` 对绑定方法不生效，用字符串路径替代：

```python
# ❌ 不稳定
patch.object(tool, "_call", return_value={...})

# ✅ 可靠
patch("dfcf_finance.DFCFFinance._call", return_value={...})
```

运行测试：
```bash
python ~/.nanobot/workspace/skills/mx-finance/test_dfcf_finance.py --live
```

## execute_code 沙箱环境（重要）

Hermes 的 `execute_code` 沙箱**不会自动注入 `~/.hermes/.env` 中的环境变量**。在沙箱中调用 `DFCFFinance()` 会因 `MX_APIKEY` 缺失而报错。

**解决方案：** 在沙箱代码中手动读取 `.env` 文件并传递 api_key：

```python
import os

# 手动读取 .env
env_vars = {}
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env_vars[k] = v

tool = DFCFFinance(api_key=env_vars['MX_APIKEY'])
```

**备选：** 使用 `terminal()` 而非 `execute_code()` 运行脚本——terminal 环境默认加载 `.env`。对于需要 3+ 次 API 调用的场景，`terminal()` + Python 脚本更可靠。

## 触发限流 vs 日配额（重要）

妙想API的"触发限流"不等于日配额用完。即使后台显示 0/500 使用量，短时间内发送**复杂 query（同时请求 6+ 个指标）**也会被 QPS 级别限流拦截，返回 `status: 500, message: '触发限流，请稍后再试'`。

**对策：**
1. 单个 query 限制在 2-3 个指标以内
2. 需要多指标时分批次调用，每批间隔 3-5 秒
3. 最简单的 query（如 `'000002 最新价'`）几乎不会触发限流

## data() 日线时间序列检索（收盘价）

`data()` 可返回每日收盘价时间序列——在 query 中**必须使用中文"至"连接日期范围**：

```python
r = tool.data('301308 江波龙 收盘价 2026-05-05至2026-06-05')
# 返回 table = {'325898': ['568.48元', ...], 'headName': ['2026-06-04', ...]}
```

**粒度控制：**
- `'日期至日期'`（中文"至"）→ DAY 粒度 ✅
- `'近一个月'` → MONTH 粒度（每月一条，不可用于技术指标计算）❌
- `'年初至今'` → 聚合值（如 YTD 涨跌幅一条）❌

**返回数据用于技术指标计算时**，收盘价带"元"后缀需 `replace('元','')` 再转 float。日期字段 `headName` 的日期顺序为最新在前。详见 lucky-bamboo → `references/dfcf-daily-price-fallback.md`。

**A/H 股价格后缀**：A股价带 `元`，H股价带 `港`（如 `"360.4港"`）。清洗时需同时移除两种后缀：`re.sub(r'[元港,]', '', s)`。若只处理 `元`，H 股价会触发 ValueError。

## API 返回字段码

`data()` 返回的指标键是**数字 ID**（如 `100000000003466` 对应 ROE、`100000000000415` 对应营收），而非人类可读名称。不同公司的同一指标可能返回**不同字段码集合**。

**实践策略：** 用自然语言 query 一次性请求多个指标，从返回值中批量提取；不需要建立完整字段码映射表。遇到空结果（`dataTableDTOList` 为空）时，换一种 query 表述重试。

### data() 五合一套餐 (v3.2 重大发现 · 2026-06-25 实测推翻旧文档)

**旧文档说"妙想不支持最高价/最低价日线序列"——已被推翻。** 五合一套餐一次返回完整 OHLC + 换手率, 跨市场全票验证通过:

```python
tool.data('000001 收盘价 最高价 最低价 开盘价 换手率 2026-03-01至2026-06-25')
# → table: {326269: 开盘, 325898: 收盘, 326339: 最高, 326386: 最低, 326699: 换手率}
#   headName: ['2026-06-24(日)', ...]  # 78天时间序列
```

**稳定字段码 (跨股票100%一致):**
| 字段码 | 含义 | 值格式 |
|--------|------|--------|
| `326269` | 开盘价 | `'382元'` |
| `325898` | 收盘价 | `'417元'` |
| `326339` | 最高价 | `'418.8元'` |
| `326386` | 最低价 | `'378.86元'` |
| `326699` | 换手率 | `'7.95%'` |

**注意:** 不能在同一 query 加「流通市值」——加了会丢失 OHLC 只返回市值。需分开查询。

**f-code 边缘票:** 次新股/冷门股的五合一返回 `{f16,f15,f17,f8}` 快照格式(单点值,非时间序列)。quick_scan v2.7 已内置分拆查询降级: 单独拉收盘+换手 → close±2% 估算高/低价。

### data(null) 崩溃修复 (v3.1 → v3.2 · 2026-06-25 实测补丁)

v3.1 声称修复了 `data:null` 但 `data()` 和 `news()` 两个方法的内部仍残留旧写法。已修复为:

```python
# 旧版 (data:null 时崩溃)
inner = raw.get("data", {})   # key存在但value=null → 返回None
status = inner.get("status", ...)  # AttributeError

# v3.2 修复
inner = raw.get("data") or {}
status = inner.get("status", ...) if inner else -1
```

同一个 `data()` 端点，**返回结构取决于 query 语义**：

| Query | table key | 数据形态 |
|-------|-----------|---------|
| `"000001 涨跌幅"` | `f3` | 实时单值 `["0.09%"]` |
| `"000001 最新价 涨跌幅 年初至今涨幅"` | `100000000006290` | 时间序列数组 + `headName` 日期 |

触发时间序列的关键词：`年初至今`、`历史`、`走势`。时间序列可用于计算 YTD、近1月、近1周等复利收益。

### 时间序列 table 结构（关键坑 · 2026-06-10）

时间序列查询返回的 `table` 字典中：
- **entity key 是数字 ID（如 `'325898'`），不是股票代码或名称**——和实时查询的 `"格力电器(000651.SZ)"` key 完全不同
- `headName` 存日期数组，格式 `'2026-06-09(日)'`，需 `replace('(日)','')` 清洗
- 价格数组带 `'元'` 后缀（可能还有 `'港'`），需正则 `re.sub(r'[元港,]', '', s)` 清洗
- 日期顺序为**最新在前**，技术指标计算需 `[::-1]` 翻转为时间顺序
- 收盘价/最高价/最低价**不能一次混合查询**——只返回收盘价。需分开三次调用
- ⚠️ **分开查询 最高价/最低价 也可能返回空**（2026-06-15 实战验证）：`'000002 最高价 2026-03-01至2026-06-15'` 返回 0 条记录，只有 `'000002 收盘价'` 稳定返回数据。KDJ 计算需依赖 fallback（收盘±2%估算高/低价）或 Sina API 实时快照

```python
# 正确用法：分开查询
closes = get_prices('000001', '收盘价')
highs  = get_prices('000001', '最高价')
lows   = get_prices('000001', '最低价')

def get_prices(code, metric):
    r = tool.data(f'{code} {metric} 2026-04-01至2026-06-10')
    tables = r['data']['data']['data']['searchDataResultDTO']['dataTableDTOList']
    for t in tables:
        tbl = t.get('table', {})
        for k, v in tbl.items():
            if k != 'headName' and isinstance(v, list) and len(v) > 10:
                return [float(re.sub(r'[元港,]', '', x)) for x in v]
    return None
```

**注意：** 实时query和时间序列query返回完全不同的table结构和嵌套层级。时间序列的嵌套路径为 `r["data"]["data"]["data"]["searchDataResultDTO"]["dataTableDTOList"]`（5层data）。

### data() 五合一 OHLC 套餐（v3.2 新增 · 2026-06-25 验证）

**推翻旧结论:** 妙想 `data()` **支持**完整的 OHLC + 换手率日线序列——但必须是组合查询，不能单独查最高价/最低价。

详见 → `references/ohlc-five-in-one.md`

### 旧版降级知识（仅收盘价 · 2026-06-15 之前 · 已被五合一套餐取代）

实测四条不同股票全部成功返回：
```
'000001 收盘价 最高价 最低价 开盘价 换手率 2026-03-01至2026-06-25'
→ 78 days, 5 metrics
  326269=开盘  325898=收盘  326339=最高  326386=最低  326699=换手率
  headName=日期 (格式 2026-06-24(日))
```

**字段码跨股票通用**（验证：佰维/澜起/美的集团/蓝思/亨通）。值带 `'元'`/`'%'` 后缀需清洗，日期顺序最新在前需 `[::-1]` 翻转。

**注意：不能在同一 query 里加「流通市值」**——加了 OHLC 会丢失只返回市值。流通市值需单独调用。

### data() 五合一 OHLC 套餐（v3.2 新增 · 2026-06-25 验证）

**推翻旧结论:** 妙想 `data()` **支持**完整的 OHLC + 换手率日线序列——但必须是组合查询，不能单独查最高价/最低价。

详见 → `references/ohlc-five-in-one.md`

### 旧版降级知识（仅收盘价 · 2026-06-15 之前 · 已被五合一套餐取代）
- `'000002 收盘价 2026-03-01至2026-06-15'` → ✅ 70条日线数据
- `'000002 最高价 2026-03-01至2026-06-15'` → ❌ 0条（`get_prices()` 返回 None）
- `'000002 最低价 2026-03-01至2026-06-15'` → ❌ 同上
- 混合查询 `'000002 收盘价 最高价 最低价 2026-05-01至2026-06-15'` → ⚠️ 仅返回收盘价（28条），最高/最低价不出现

**影响：** KDJ 计算需要高/低价，妙想 API 无法提供完整的 KDJ 数据。需要 push2his（`kline/get`）或其他数据源获取 OHLC。fallback_scan.py 用 `close±2%` 估算高/低价，KDJ 值仅供参考。

详见 → `references/data_timeseries.md`（含 YTD 复利计算模板、批量多股对比脚本）

## 数据源优先级（强制）

**妙想优先，公开API只做补充。** 顺序不要搞反：

1. **先试 `data()`**（妙想 MX_APIKEY）——所有日级别行情、财务数据、资金流向、融资融券
2. **再试 `news()` / `screen()`** ——资讯和选股同样走妙想
3. **最后才用公开API** ——仅限妙想不支持的数据类型：分钟K线（`kline/get`）、分时数据（`trends2/get`）、全A实时筛选（`clist/get`）

判断标准：日级别及以上粒度 → 妙想。分钟级别 → 公开API。资金流向是日级别的 → 妙想。

## 公开API补充（分钟线/分时数据）

妙想API不支持分钟K线或分时数据。需要分钟级数据时，使用东方财富公开API（`push2his.eastmoney.com`，无需密钥）：

| 端点 | 用途 |
|------|------|
| `clist/get` | 全A股列表+实时筛选（字段：f2价格/f3涨幅/f8换手/f10量比） |
| `trends2/get` | 1分钟分时数据（含VWAP均价线） |
| `kline/get` | 任意周期K线（klt=1/5/15/30/60/101） |

**网络注意**：WSL环境用 `urllib.request` + HTTPS直连，不用 `requests` 库，不用代理。

详见 → `references/eastmoney_public_api.md`

## screen() 自然语言限制

`screen()` 不接受纯行业名称（如"数字芯片设计行业的上市公司"），需使用**量化条件**：
- ✅ `"市盈率小于50 毛利率大于20% 的半导体股票"`
- ❌ `"数字芯片设计行业的上市公司"`

`screen()` 返回空列表且 `status: 100` 时，说明条件解析失败——改用 `data()` 逐只查询。

`screen()` 对行业名称（如"广告营销行业"）也会返回 `status: 100, "参数校验失败，选股条件关键词不能为空"`。不要反复重试——直接切 `web_search()`。

## data() 对可比公司的静默返回

对目标公司（如五粮液 000858）查询正常返回多 table，但相同 query 格式对其他公司可能返回
`dataTableDTOList: []`（`success: true` 但无数据）。不是 API 挂了——是东方财富 query 解析对非热门标的弱匹配。

```python
tool.data('300058 蓝色光标 最新价 总市值')  # → success=True, 0 tables
tool.data('300058 总市值')                    # → 可能同样 0 tables
```

**对策：**
1. 目标公司优先用 `data()`（大概率成功）
2. 可比公司数据不行就立即切 `web_search()` + `web_extract()` 回退
3. 不要花超过 2 轮尝试修复——web_search 拿到的近似值足够支撑可比分析

| `/query` 接口参数是 `toolQuery` 不是 `query` | 其他接口用 `query`，这个接口特殊 | ✅ 已处理 |
| `success` 字段判断需结合 `status==0` | 东方财富返回 `success:true` 但 `status:100` 也算失败 | ✅ 已处理 |
| 自选股 API 需要东方财富通行证 | 无账号返回空列表 | 不在代码侧解决 |

## data() 表格结构双形态（关键坑）

`data()` 返回的 `dataTableDTOList` 有两种**互斥**的数据结构，取决于 query 语义：

### 形态 A：`headList` + `dataTableDTORows`（财务时间序列）

```python
# 路径：t["headList"] + t["dataTableDTORows"][i]["dataTableDTOCells"]
# 典型 query：多指标财务数据（营业总收入 归属净利润...）
# 问题：headList 和 rows 可能同时为空数组（dataTableDTOList 有 7 个 table 全是空）→ 见形态 B
```

### 形态 B：`table` 字典（行情实时数据）

```python
# 路径：t["table"] = {"格力电器(000651.SZ)": ["40.28"], "headName": ["2026-05-27"]}
# 典型 query：最新价 总市值 PE(TTM) PB 等实时指标
# entity name → value array 的映射，headName 存时间戳
```

**解析代码必须同时处理两种形态，先探测再解析：**

```python
for t in tables:
    tbl = t.get('table', {})
    if tbl:
        # 形态 B：直接遍历 entity keys
        hdr = tbl.get('headName', [])
        for k, v in tbl.items():
            if k == 'headName': continue
            print(f'{k}: {v} ({hdr})')
    else:
        # 形态 A：传统 headList + rows
        for h in t.get('headList', []):
            ...
```

**不同 query 返回的是互斥的形态——同一请求不会混合。** 先探测 `table` 键，不存在再走 `headList` 路径。只走一条路的代码会在另一种 query 下全部返回空。

### 多标的查询（重要）

当 query 匹配到多只股票（如格力电器同时有 A 股 000651 + H 股 06613），`table` 会同时返回两者的数据：
```python
{"格力电器(06613.HK)": ["23.560"], "格力电器(000651.SZ)": ["40.28"], "headName": ["2026-05-27"]}
```
需根据后缀 `.SZ` / `.HK` 区分 A/H 股数据。

## 版本历史

### v2.3 (2026-05-27)
- 新增「data() 表格结构双形态」章节 — 文档化 `table` 字典 vs `headList`+rows 两种互斥结构
- 新增多标的查询处理说明（A/H 股同时返回时的区分方法）

### v2.2 (2026-05-21)
- 新增 `references/data_timeseries.md` — 时间序列 vs 实时数据结构差异、YTD 复利计算模板、批量多股对比脚本
- SKILL.md 新增「data() 时间序列 vs 实时数据」章节，区分 `f3`（实时）vs `100000000006290`（时间序列）

### v2.1 (2026-04-16)
- 修正 `/query` 接口使用 `toolQuery` 参数（核心 bug 修复）
- 修正 `success` 判断逻辑（`status==0` 而非只看 `success` 字段）
- 修正自选股删除 query 语句（中文语义正确）
- 修正 `WATCHLIST_MANGE` → `WATCHLIST_MGR` 拼写
- `route()` 路由关键词增补 `ROE`

### v2.0 (2026-04-16)
- 整合 Hermes + nanobot 两版优点
- 新增 `news` 场景（nanobot 初版漏掉）
- OOP 封装 + 统一响应格式 + timestamp
- 自动路由 `route()` 方法
