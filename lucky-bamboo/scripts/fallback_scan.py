#!/usr/bin/env python3
"""fallback_scan.py — Use dfcf data() daily closes to calculate BOLL/KDJ/MACD.

Trigger: push2his.eastmoney.com is unreachable (WSL RemoteDisconnected).
Fallback: dfcf妙想 data() → daily close prices → manual indicator calculation.

Usage:
  python fallback_scan.py 688525 佰维存储
  python fallback_scan.py 688008 澜起科技

Requires: DFCF finance tool (MX_APIKEY in env), numpy.
"""

import os
import sys
import numpy as np


def parse_prices(raw_values):
    """Parse dfcf data() price strings to float list (chronological order).
    Filters out HKD prices (ending with '港')."""
    result = []
    for v in reversed(raw_values):
        # Skip HKD-denominated prices (A+H dual-listed stocks)
        if '港' in v:
            continue
        clean = v.replace('元', '')
        if clean:
            result.append(float(clean))
    return result


def calc_boll(close, n=20):
    """BOLL(20, ±2σ). Returns (mid, upper, lower)."""
    mid = np.mean(close[-n:])
    std = np.std(close[-n:], ddof=0)
    return mid, mid + 2 * std, mid - 2 * std


def calc_kdj(close, n=14, m1=3, m2=3):
    """KDJ(14,3,3) using only close prices (RSV approximation without high/low).

    Accuracy: directionally valid, underestimates true volatility.
    """
    k_vals, d_vals, j_vals = [], [], []
    for i in range(len(close)):
        if i < n - 1:
            k_vals.append(50)
            d_vals.append(50)
            j_vals.append(50)
            continue
        hh = max(close[i - n + 1 : i + 1])
        ll = min(close[i - n + 1 : i + 1])
        rsv = (close[i] - ll) / (hh - ll) * 100 if hh != ll else 50
        k = (2 / 3) * k_vals[-1] + (1 / 3) * rsv
        d = (2 / 3) * d_vals[-1] + (1 / 3) * k
        j = 3 * k - 2 * d
        k_vals.append(k)
        d_vals.append(d)
        j_vals.append(j)
    return k_vals[-1], d_vals[-1], j_vals[-1]


def calc_macd(close, fast=12, slow=26, signal=9):
    """MACD(12,26,9). Returns (dif, dea, hist, prev_hist)."""
    ema_fast = close[0]
    ema_slow = close[0]
    dea = 0
    prev_hist = 0
    for p in close:
        ema_fast = p * 2 / (fast + 1) + ema_fast * (1 - 2 / (fast + 1))
        ema_slow = p * 2 / (slow + 1) + ema_slow * (1 - 2 / (slow + 1))
        dif = ema_fast - ema_slow
        prev_hist = 2 * (dif - dea)
        dea = dif * 2 / (signal + 1) + dea * (1 - 2 / (signal + 1))
    hist = 2 * (dif - dea)
    return dif, dea, hist, prev_hist


def check_conditions(close):
    """Run the four-condition check. Returns dict of results."""
    mid, upper, lower = calc_boll(close, 20)
    k, d, j = calc_kdj(close, 14)
    dif, dea, hist, prev_hist = calc_macd(close, 12, 26, 9)
    close_now = close[-1]

    c1 = close_now <= mid
    c2 = k < 30
    c3 = j < 20
    c4 = hist < 0 and abs(hist) < abs(prev_hist)

    return {
        "close": close_now,
        "boll_mid": round(mid, 1),
        "boll_upper": round(upper, 1),
        "boll_lower": round(lower, 1),
        "k": round(k, 1),
        "d": round(d, 1),
        "j": round(j, 1),
        "dif": round(dif, 2),
        "dea": round(dea, 2),
        "hist": round(hist, 2),
        "prev_hist": round(prev_hist, 2),
        "c1_close_below_mid": c1,
        "c2_k_below_30": c2,
        "c3_j_below_20": c3,
        "c4_macd_green_narrow": c4,
        "lights": sum([c1, c2, c3, c4]),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python fallback_scan.py <code> [name]")
        sys.exit(1)

    code = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else code

    # dfcf_finance lives in Fugui-research-lab, not on default PYTHONPATH
    sys.path.insert(0, os.path.expanduser('~/Fugui-research-lab/fugui-finance-package/dfcf_finance'))
    try:
        from dfcf_finance import DFCFFinance
    except ModuleNotFoundError:
        print("Error: dfcf_finance module not found. Set MX_APIKEY in ~/.hermes/.env", file=sys.stderr)
        print("and ensure ~/Fugui-research-lab/fugui-finance-package/dfcf_finance/ exists.", file=sys.stderr)
        sys.exit(2)

    tool = DFCFFinance()
    r = tool.data(f"{code} {name} 收盘价 2026-03-01至2026-06-13")
    tables = (
        r.get("data", {})
        .get("data", {})
        .get("data", {})
        .get("searchDataResultDTO", {})
        .get("dataTableDTOList", [])
    )

    close_raw = None
    for t in tables:
        tbl = t.get("table", {})
        if not tbl:
            continue
        for k, v in tbl.items():
            if k == "headName":
                continue
            # Skip HKD tables (A+H dual-listed stocks like 688008/澜起)
            if isinstance(v, list) and v and ('港元' in str(v[0])):
                continue
            close_raw = v
            break
        if close_raw:
            break

    if not close_raw:
        print("ERROR: No close price data found")
        sys.exit(1)

    close = parse_prices(close_raw)
    result = check_conditions(close)

    print(f"\n{'='*50}")
    print(f"  {name} ({code}) — fallback_scan")
    print(f"{'='*50}")
    print(f"\n📊 BOLL(20): 上{result['boll_upper']} 中{result['boll_mid']} 下{result['boll_lower']}")
    print(f"   收盘: {result['close']} | 条件1 ≤中轨: {'✅' if result['c1_close_below_mid'] else '❌'}")
    print(f"\n📊 KDJ(14): K={result['k']} D={result['d']} J={result['j']}")
    print(
        f"   条件2 K<30: {'✅' if result['c2_k_below_30'] else '❌'} | 条件3 J<20: {'✅' if result['c3_j_below_20'] else '❌'}"
    )
    print(f"\n📊 MACD: DIF={result['dif']} DEA={result['dea']} 柱={result['hist']}")
    print(
        f"   前日柱={result['prev_hist']} | 条件4 绿柱收窄: {'✅' if result['c4_macd_green_narrow'] else '❌'}"
    )
    print(f"\n🏮 四灯: {result['lights']}/4")


if __name__ == "__main__":
    main()
