# dfcf 妙想API 日线价格回退方案

**触发条件：** push2his.eastmoney.com 不可达（WSL RemoteDisconnected / rc=102）

## 可用数据源对比

| 源 | 端点 | 返回 | 限制 |
|---|------|------|------|
| push2his | 公开API | 完整OHLCV | WSL常 RemoteDisconnected |
| dfcf妙想 | `data()` | 收盘价 + 市值 | 无OHLC，有QPS限流 |

## dfcf 日线收盘价检索方法

```python
# 触发每日粒度：必须在 query 中包含日期范围
r = tool.data('CODE 名称 收盘价 YYYY-MM-DD至YYYY-MM-DD')

# 响应结构
d = r['data']['data']['data']['searchDataResultDTO']['dataTableDTOList'][0]
table = d['table']
# table = {'325898': ['305.15元', '288.5元', ...], 'headName': ['2026-06-09(日)', '2026-06-08(日)', ...]}
```

**关键坑（2026-06-10 实战验证）：**

1. **Entity key 是数字 ID**（如 `'325898'`），不是股票代码或名称。遍历 `table` 时先找非 `headName` 的 key。

2. **价格字符串需多重清理**：
   - 常规：`replace('元','')` + `replace(',','')`
   - A+H 股会出现 `'360.4港'` 后缀 → 需 `replace('港','')`
   - 统一清理：`re.sub(r'[元港,]', '', s)`

3. **日期格式**：`headName` 值为 `'2026-06-09(日)'` — 需 `replace('(日)','')` 才能解析

4. **时间序列顺序**：最新日期在前（reverse chronological），计算指标前需 `[::-1]` 反转

5. **收盘价/最高价/最低价需分别查询**：单次 `data()` 同时请求三个指标时，可能只返回收盘价（其余落入 summary table 而非 time series）。可靠做法：分三次调用 `data()`，每次只请求一个指标。

6. **备用脚本 `fallback_scan.py` 的 import 坑**：脚本直接 `from dfcf_finance import DFCFFinance`，需确保 `dfcf_finance.py` 在 PYTHONPATH 中。推荐用 `execute_code` 或 `terminal` + 绝对路径 import：
```python
sys.path.insert(0, os.path.expanduser('~/Fugui-research-lab/fugui-finance-package/dfcf_finance'))
from dfcf_finance import DFCFFinance
```

## 无OHLC下的KDJ/MACD近似

只用收盘价序列时：
- **BOLL(20)**：直接可算（只需收盘价）
- **KDJ**：需要高/低价。用收盘价 ±2% 近似可估方向，但精确值需分别查询 `最高价`/`最低价`。实战验证：分别 query 后先确认 `len(highs)==len(closes)` 再合并。
- **MACD**：EMA12/EMA26/DEA9 都只依赖收盘价，完全可算

近似精度：BOLL 准确 → MACD 准确 → KDJ 偏低估（缺少日内极值）

## 一键执行

```bash
cd ~/.hermes/skills/finance/lucky-bamboo/scripts
python fallback_scan.py 000001 平安银行
python fallback_scan.py 000002 格力电器
```

`fallback_scan.py` 完成：取 dfcf data() 收盘价 → numpy 计算 BOLL/KDJ/MACD → 输出四灯状态。
日期范围硬编码为 `2026-03-01至2026-06-08`，如需更长历史修改脚本内的 query 字符串。
