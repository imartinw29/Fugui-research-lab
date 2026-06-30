# 妙想 data() 时间序列 → 自算 BOLL/MACD（三级降级）

当 push2his 不可达 + fallback_scan.py 缺 dfcf_finance 模块时使用。

## 工作原理

1. 用妙想 `data()` 拉取收盘价时间序列（query 格式：`"000001 佰维 收盘价 YYYY-MM-DD至YYYY-MM-DD"`）
2. numpy 自算 BOLL(20,2) + MACD(12,26,9)
3. **KDJ 不可算**（需要高/低价，妙想收盘价查询不含此数据）

## 数据结构

妙想 data() 时间序列返回路径：
```python
r['data']['data']['data']['searchDataResultDTO']['dataTableDTOList'][0]['table']
```

table 结构：
```python
{
    "325898": ["305.15元", "288.5元", "311元", ...],  # key 是数字 ID，非股票代码
    "headName": ["2026-06-09(日)", "2026-06-08(日)", ...]  # 日期倒序
}
```

## 价格清洗

价格值可能带 `元` 或 `港` 后缀，需清洗：
```python
import re
def clean_price(s):
    return float(re.sub(r'[元港,]', '', s))
```

## 完整计算脚本（模板）

```python
import sys, json, numpy as np, re
sys.path.insert(0, '~/Fugui-research-lab/fugui-finance-package/dfcf_finance')
from dfcf_finance import DFCFFinance

tool = DFCFFinance()
r = tool.data('000001 佰维 收盘价 2026-04-01至2026-06-10')

tables = r['data']['data']['data']['searchDataResultDTO']['dataTableDTOList']
tbl = tables[0]['table']
hdr = tbl.get('headName', [])

prices = None
for k, v in tbl.items():
    if k != 'headName':
        prices = [clean_price(x) for x in v]
        break

closes = np.array(prices[::-1])  # 反转为时间升序

# BOLL
ma = np.mean(closes[-20:])
std = np.std(closes[-20:], ddof=1)
upper, lower = ma + 2*std, ma - 2*std

# MACD
ema12 = ema26 = np.zeros(len(closes))
ema12[0] = ema26[0] = closes[0]
for i in range(1, len(closes)):
    ema12[i] = (2/13)*closes[i] + (11/13)*ema12[i-1]
    ema26[i] = (2/27)*closes[i] + (25/27)*ema26[i-1]

dif = ema12 - ema26
dea = np.zeros(len(closes))
dea[0] = dif[0]
for i in range(1, len(closes)):
    dea[i] = (2/10)*dif[i] + (8/10)*dea[i-1]

macd_hist = 2*(dif - dea)

# 信号判定
cond_bb = closes[-1] <= ma
recent = macd_hist[-5:]
cond_macd = np.all(recent < 0) and recent[-1] > recent[-2]  # 绿柱收窄
```

## 限制

- **无 KDJ**：KDJ(14,3,3) 需要高/低价，收盘价序列不可算
- **无历史 DIF/DEA 交叉点**：EMA 起算点取首个收盘价，前20期偏差较大但不影响近期信号
- **数据点要求**：至少 26 个交易日（20期 BOLL + 足够 MACD 平滑）
- **妙想限流**：简单 query（仅收盘价）几乎不触发限流，批量 5 只无问题

## 运行环境

用 `terminal()` 而非 `execute_code()`——terminal 自动加载 `.env` 中的 `MX_APIKEY`。脚本放在临时位置即可，无需保存为永久文件。
