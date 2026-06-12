#!/usr/bin/env python3
"""lucky-bamboo quick scan v2: 四灯 + 筹码峰

Usage: python quick_scan.py <secid>  (e.g. 1.688008 for 澜起科技)
       secid = market(1=SH, 0=SZ) + '.' + code

新增：筹码峰数据（平均成本、获利比例、筹码集中度）
需要 MX_APIKEY 环境变量；无 key 时跳过筹码查询。
"""

import json, math, os, re, ssl, sys, urllib.request
from datetime import datetime


def fetch_kline(secid: str) -> tuple:
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}"
        f"&fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&klt=101&fqt=0&end={datetime.now().strftime('%Y%m%d')}&lmt=30"
    )
    with urllib.request.urlopen(url, timeout=10, context=ssl._create_unverified_context()) as resp:
        raw = json.loads(resp.read())
    if raw.get("rc") != 0 or not raw.get("data") or not raw["data"].get("klines"):
        raise RuntimeError(f"East Money API error: {raw.get('rc')}")
    name = raw["data"]["name"]
    klines = raw["data"]["klines"]
    data = []
    for line in klines:
        parts = line.split(",")
        data.append({
            "date": parts[0], "open": float(parts[1]), "close": float(parts[2]),
            "high": float(parts[3]), "low": float(parts[4]),
        })
    return name, data


def calc_boll(closes, period=20, sigma=2):
    window = closes[-period:]
    ma = sum(window) / period
    std = math.sqrt(sum((c - ma) ** 2 for c in window) / period)
    return ma + sigma * std, ma, ma - sigma * std


def calc_kdj(data, period=14):
    k_prev = d_prev = 50.0
    k_vals, d_vals = [], []
    for i in range(period, len(data)):
        window = data[i - period + 1 : i + 1]
        ll = min(d["low"] for d in window)
        hh = max(d["high"] for d in window)
        rsv = (data[i]["close"] - ll) / (hh - ll) * 100 if hh != ll else 50
        k_new = 2 / 3 * k_prev + 1 / 3 * rsv
        d_new = 2 / 3 * d_prev + 1 / 3 * k_new
        k_vals.append(k_new); d_vals.append(d_new)
        k_prev, d_prev = k_new, d_new
    k, d = k_vals[-1], d_vals[-1]
    return k, d, 3 * k - 2 * d


def calc_macd(closes, fast=12, slow=26, signal=9):
    ema_f = closes[0]; ema_s = closes[0]
    dif_vals = []
    for c in closes:
        ema_f = c * 2 / (fast + 1) + ema_f * (1 - 2 / (fast + 1))
        ema_s = c * 2 / (slow + 1) + ema_s * (1 - 2 / (slow + 1))
        dif_vals.append(ema_f - ema_s)
    dea = dif_vals[0]
    dea_vals = []
    for d in dif_vals:
        dea = d * 2 / (signal + 1) + dea * (1 - 2 / (signal + 1))
        dea_vals.append(dea)
    macd_vals = [2 * (d - de) for d, de in zip(dif_vals, dea_vals)]
    return dif_vals[-1], dea_vals[-1], macd_vals[-1], macd_vals[-2]


def fetch_chip(code: str) -> dict | None:
    """拉取筹码峰数据（需要 MX_APIKEY）"""
    try:
        sys.path.insert(0, os.path.expanduser(
            '~/Fugui-research-lab/fugui-finance-package/dfcf_finance'))
        from dfcf_finance import DFCFFinance
        tool = DFCFFinance()
        r = tool.data(f'{code} 筹码分布 获利盘比例')
        tables = r.get('data',{}).get('data',{}).get('data',{}).get(
            'searchDataResultDTO',{}).get('dataTableDTOList',[])
        
        chip = {}
        for t in tables:
            tbl = t.get('table', {})
            if not tbl:
                continue
            for k, v in tbl.items():
                if k == 'headName':
                    continue
                val = v[0] if isinstance(v, list) and len(v) > 0 else v
                try:
                    chip[k] = float(re.sub(r'[%元,]', '', str(val)))
                except:
                    pass
        
        return {
            'avg_cost': chip.get('010000_CMPJCB'),
            'profit_pct': chip.get('010000_HLP'),
            'conc_70': chip.get('010000_CMFB_461_JZD70'),
            'conc_90': chip.get('010000_CMFB_461_JZD90'),
        }
    except Exception:
        return None


def scan(secid: str):
    name, data = fetch_kline(secid)
    closes = [d["close"] for d in data]
    today = data[-1]
    
    upper, mid, lower = calc_boll(closes)
    k, d, j = calc_kdj(data)
    dif, dea, macd_bar, macd_prev = calc_macd(closes)
    
    bb_pos = (today["close"] - lower) / (upper - lower) * 100 if upper != lower else 50
    
    # Extract code from secid (e.g. 1.688008 → 688008)
    code = secid.split('.')[-1]
    chip = fetch_chip(code)
    
    c1 = today["close"] <= mid
    c2 = k < 30
    c3 = j < 20
    c4 = macd_bar > macd_prev and macd_bar < 0
    passed = sum([c1, c2, c3, c4])
    
    print(f"{'='*60}")
    print(f"  {name}  {secid}  |  {today['date']}  收盘: {today['close']:.2f}")
    print(f"{'='*60}")
    print(f"  BOLL(20,2): 上={upper:.2f} 中={mid:.2f} 下={lower:.2f}  位置:{bb_pos:.0f}%")
    print(f"  KDJ(14,3):  K={k:.1f}  D={d:.1f}  J={j:.1f}")
    print(f"  MACD(12,26,9): DIF={dif:.2f} DEA={dea:.2f} 柱={macd_bar:.3f}  {'金叉' if dif>dea else '死叉'}")
    
    if chip and chip['avg_cost']:
        print(f"  {'─'*50}")
        print(f"  📊 筹码峰: 均价={chip['avg_cost']:.2f}  获利={chip['profit_pct']:.1f}%  "
              f"70%集中={chip['conc_70']:.1f}%  90%集中={chip['conc_90']:.1f}%")
        if today['close'] < chip['avg_cost']:
            disc = (1 - today['close'] / chip['avg_cost']) * 100
            print(f"     💰 当前价在均价之下 {disc:.1f}% —— 筹码低位，安全边际好")
        else:
            prem = (today['close'] / chip['avg_cost'] - 1) * 100
            print(f"     ⚠️  当前价在均价之上 {prem:.1f}% —— 获利盘有兑现压力")
    
    print(f"  {'─'*50}")
    print(f"  ① 收盘≤中轨 ({today['close']:.2f}≤{mid:.2f})  {'✅' if c1 else '❌'}")
    print(f"  ② K<30        ({k:.1f}<30)        {'✅' if c2 else '❌'}")
    print(f"  ③ J<20        ({j:.1f}<20)        {'✅' if c3 else '❌'}")
    print(f"  ④ MACD绿柱收窄 ({macd_bar:.3f}>{macd_prev:.3f})  {'✅' if c4 else '❌'}")
    print(f"  {'─'*50}")
    
    if passed == 4:
        print(f"  🟢 四灯全亮！买入信号")
        if chip and chip['avg_cost'] and today['close'] < chip['avg_cost']:
            print(f"  🟢 筹码低位确认 —— 双重共振")
    else:
        print(f"  🔴 不满足 ({passed}/4)")
    
    print()
    return passed == 4


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_scan.py <secid>  (e.g. 1.688008)")
        sys.exit(1)
    try:
        scan(sys.argv[1])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
