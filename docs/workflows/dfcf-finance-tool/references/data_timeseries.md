# data() 时间序列 vs 实时数据 — 结构差异与 YTD 计算

## 核心区别

`data()` 的返回结构**取决于 query 语义**，不是固定的：

| Query 类型 | 示例 | table key | 数据结构 |
|-----------|------|-----------|---------|
| 实时单点 | `"000001 涨跌幅"` | `f3` | 单值 `["0.09%"]` |
| 时间序列 | `"000001 最新价 涨跌幅 年初至今涨幅"` | `100000000006290` | 数组 `["0%","1.01%",...]` + `headName` |

**规则：** query 里包含「年初至今」「历史」「走势」等时间维度关键词 → 触发时间序列返回。

## 时间序列响应结构

```python
# 深度嵌套路径（5层 data）
dto_list = r["data"]["data"]["data"]["searchDataResultDTO"]["dataTableDTOList"]
dto = dto_list[0]

# 关键字段
table = dto["table"]          # {"100000000006290": [...], "headName": [...]}
raw = dto["rawTable"]         # {"100000000006290": ["0.0","1.011...",...]}
dates = table["headName"]     # ["2026-05-21","2026-05-20",...,"2026-01-05"]

# 找到数据key（排除 headName）
data_key = [k for k in table if k != "headName"][0]
values_raw = raw[data_key]    # list of numeric strings
values = [float(v) for v in values_raw]

# 值顺序：dates[0]=最新, values[0]=最新日涨跌幅
# 最新日（未收盘）通常为 "0.0" / "0%"
```

## 已知字段码

| 字段码 | 含义 | 出现场景 |
|--------|------|---------|
| `100000000006290` | 日涨跌幅(%) 时间序列 | 含"年初至今涨幅"的query |
| `f3` | 实时涨跌幅(%) | 纯实时query |
| `headName` | 日期标签 | 时间序列query的伴生字段 |

> 注：财务指标字段码（营收/净利润/ROE等）随公司和query变化，见 SKILL.md 已知坑。

## YTD 涨幅计算

```python
def compute_ytd(values, dates):
    """
    values: 每日涨跌幅(%) 列表，values[0]=最新日
    dates: 日期列表，dates[0]=最新日，dates[-1]=最早日
    
    从最早日（2026-01-05首个交易日）向最新日复利计算。
    跳过 values[i]==0.0（当日未收盘/停牌）。
    """
    ytd_cum = 1.0
    for i in range(len(values)-1, -1, -1):  # 从最旧到最新
        if values[i] != 0.0:
            ytd_cum *= (1 + values[i] / 100)
    return (ytd_cum - 1) * 100  # 返回百分比

# 同理可计算 近1月(~20日)、近1周(~5日)
def compute_window(values, window_size, skip_today=True):
    """window_size 个交易日（从最新端取）"""
    start = 1 if skip_today else 0  # 跳过当天0%
    cum = 1.0
    for v in values[start:start+window_size]:
        if v != 0.0:
            cum *= (1 + v / 100)
    return (cum - 1) * 100
```

## 批量多股对比脚本模板

```python
# 在 execute_code 中批量查询多只股票的YTD
stocks = [("000001","平安银行"), ("000002","格力电器"), ...]

for code, name in stocks:
    r = tool.data(f"{code} {name} 最新价 涨跌幅 年初至今涨幅 总市值")
    dto_list = r["data"]["data"]["data"]["searchDataResultDTO"]["dataTableDTOList"]
    if not dto_list: continue
    
    dto = dto_list[0]
    raw = dto["rawTable"]
    data_key = [k for k in dto["table"] if k != "headName"][0]
    values = [float(v) for v in raw[data_key]]
    
    ytd = compute_ytd(values, dto["table"]["headName"])
    print(f"{name}: YTD={ytd:+.2f}%")
```

## 注意事项

1. **data() 返回的日期范围有限** — 此 session 中只拉到 2026-01-05 起，约89个交易日。近1年/近52周数据可能超出范围，需用 web_search + investing.com 等外部数据源补充。
2. **最新交易日 values[0] 通常为 0.0** — 盘中查询时当日涨跌幅尚未确定。计算窗口收益时跳过。
3. **不同 query 触发不同 table key** — `"涨跌幅"` 单独查询返回 `f3`（实时单值）；加上 `"年初至今涨幅"` 返回 `100000000006290`（时间序列）。不要假设 key 固定。
