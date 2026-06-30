---
name: dfcf-finance-tool
title: 东方财富金融工具
description: 5场景全覆盖 — 行情查询、资讯搜索、智能选股、自选股管理。统一接口，OOP封装，自动路由，Hermes/nanobot/OpenClaw 通用。
env:
  MX_APIKEY:
    description: 东方财富妙想 API Key（从东方财富妙想Skills页面获取）
    required: true
---

# dfcf-finance-tool 东方财富金融工具 v2.1

## 五场景

| 场景 | 方法 | 接口参数 | 说明 |
|------|------|----------|------|
| 行情/财务 | `data(query)` | `toolQuery` | 个股、板块、指数行情与财务指标 |
| 资讯搜索 | `news(query)` | `query` | 新闻、公告、研报、政策 |
| 智能选股 | `screen(query)` | `query` | 自然语言条件筛选 |
| 自选股查询 | `watchlist_get()` | `query` | 获取已添加的自选股 |
| 自选股管理 | `watchlist_manage(action, stock)` | `query` | 添加 / 删除 |

**注意**：`data()` 场景使用 `toolQuery` 参数，其他场景均使用 `query`。
这是东方财富妙想 API 的原始设计，不是 bug，已在代码中正确区分。

## 自动路由

`route(query)` 自动判断场景：

```
"贵州茅台最新股价"           → data()
"人工智能板块新闻"           → news()
"市盈率小于20的银行股"       → screen()
"查看我的自选股"             → watchlist_get()
"把宁德时代添加到自选股"     → watchlist_manage("add", "宁德时代")
"从自选股删除比亚迪"         → watchlist_manage("delete", "比亚迪")
```

## API 端点

```
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

## CLI 用法

```bash
python dfcf_finance.py 贵州茅台最新股价
python dfcf_finance.py 人工智能板块新闻
python dfcf_finance.py 市盈率小于20的银行股
```

## 已知坑

- `/query` 端点 **必须** 用 `toolQuery` 作参数名，不是 `query`；写错会返回 `{"error": "未知错误"}` 或 `114` 状态码
- nanobot 侧旧版 `mx_finance.py` 与 `dfcf_finance.py` 并存，只有 `dfcf_finance.py` 是 v2.1，旧文件已删除

## 跨平台同步规则

**Hermes 侧是主开发侧**。每次在 Hermes 上修复 bug 或升级版本后，必须同步到 nanobot：

```bash
# 同步 dfcf_finance.py（Hermes → nanobot）
cp ~/.hermes/skills/dfcf-finance-tool/scripts/dfcf_finance.py \
   ~/.nanobot/workspace/skills/mx-finance/dfcf_finance.py

# nanobot 端需要兼容别名（已加在文件末尾）
MXFinance = DFCFFinance
```

## screen() 崩溃修复（两边同步）

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

## API 返回字段码

`data()` 返回的指标键是**数字 ID**（如 `100000000003466` 对应 ROE、`100000000000415` 对应营收），而非人类可读名称。不同公司的同一指标可能返回**不同字段码集合**。

**实践策略：** 用自然语言 query 一次性请求多个指标，从返回值中批量提取；不需要建立完整字段码映射表。遇到空结果（`dataTableDTOList` 为空）时，换一种 query 表述重试。

## data() 时间序列 vs 实时数据（重要）

同一个 `data()` 端点，**返回结构取决于 query 语义**：

| Query | table key | 数据形态 |
|-------|-----------|---------|
| `"000001 涨跌幅"` | `f3` | 实时单值 `["0.09%"]` |
| `"000001 最新价 涨跌幅 年初至今涨幅"` | `100000000006290` | 时间序列数组 + `headName` 日期 |

触发时间序列的关键词：`年初至今`、`历史`、`走势`。时间序列可用于计算 YTD、近1月、近1周等复利收益。

**注意：** 实时query和时间序列query返回完全不同的table结构和嵌套层级。时间序列的嵌套路径为 `r["data"]["data"]["data"]["searchDataResultDTO"]["dataTableDTOList"]`（5层data）。

详见 → `references/data_timeseries.md`（含 YTD 复利计算模板、批量多股对比脚本）

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

## 版本历史

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
