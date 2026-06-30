#!/usr/bin/env python3
"""lucky-bamboo 实时买入信号筛选器

从东方财富日线 API 拉数据，计算 BOLL(20,2)/KDJ(14,3,3)/MACD(12,26,9)，
对照 v2.0 买入条件输出判定。

用法:
  python screen_buy_signal.py 000001          # 平安银行
  python screen_buy_signal.py 000001 000002   # 多票批量
  python screen_buy_signal.py --pool          # 跑已回测池全量

输出: 每票一行，含四条件判定 + 总分 + 关键指标
"""

import sys, json, math, urllib.request

BOLL_N = 20
KDJ_N = 14
MACD_FAST, MACD_SLOW, MACD_SIG = 12, 26, 9

POOL = {
}


def fetch_klines(code: str, market: int = 0, limit: int = 30) -> list[dict]:
    """拉取东方财富日线，返回 [{date, open, close, high, low}, ...]"""
    secid = f"{market}.{code}"
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}&fields1=f1,f2&fields2=f51,f52,f53,f54,f55&"
        f"klt=101&fqt=0&lmt={limit}"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        raw = json.loads(resp.read())
    if not raw.get("data") or not raw["data"].get("klines"):
        return []
    out = []
    for line in raw["data"]["klines"]:
        parts = line.split(",")
        out.append({
            "date": parts[0],
            "open": float(parts[1]),
            "close": float(parts[2]),
            "high": float(parts[3]),
            "low": float(parts[4]),
        })
    return out


def calc_boll(closes: list[float]) -> tuple[float, float, float]:
    ma = sum(closes[-BOLL_N:]) / BOLL_N
    std = math.sqrt(sum((c - ma) ** 2 for c in closes[-BOLL_N:]) / BOLL_N)
    return ma + 2 * std, ma, ma - 2 * std


def calc_kdj(data: list[dict]) -> tuple[float, float, float]:
    kp, dp = 50.0, 50.0
    n = len(data)
    for i in range(KDJ_N, n):
        window = data[i - KDJ_N + 1 : i + 1]
        ll = min(d["low"] for d in window)
        hh = max(d["high"] for d in window)
        rsv = (data[i]["close"] - ll) / (hh - ll) * 100 if hh != ll else 50
        kn = 2 / 3 * kp + 1 / 3 * rsv
        dn = 2 / 3 * dp + 1 / 3 * kn
        kp, dp = kn, dn
    j = 3 * kp - 2 * dp
    return kp, dp, j


def calc_macd(closes: list[float]) -> tuple[float, float, float, float]:
    e12 = closes[0]
    e26 = closes[0]
    ev12, ev26 = [], []
    for c in closes:
        e12 = c * 2 / (MACD_FAST + 1) + e12 * (1 - 2 / (MACD_FAST + 1))
        e26 = c * 2 / (MACD_SLOW + 1) + e26 * (1 - 2 / (MACD_SLOW + 1))
        ev12.append(e12)
        ev26.append(e26)
    dif = [a - b for a, b in zip(ev12, ev26)]
    dea = dif[0]
    deas = []
    for v in dif:
        dea = v * 2 / (MACD_SIG + 1) + dea * (1 - 2 / (MACD_SIG + 1))
        deas.append(dea)
    macd_vals = [2 * (d - de) for d, de in zip(dif, deas)]
    return dif[-1], deas[-1], macd_vals[-1], macd_vals[-2]


def check(code: str, market: int = 0, quiet: bool = False) -> dict | None:
    data = fetch_klines(code, market, limit=30)
    if len(data) < 26:
        if not quiet:
            print(f"{code}: 数据不足")
        return None

    closes = [d["close"] for d in data]
    upper, mid, lower = calc_boll(closes)
    k, d, j = calc_kdj(data)
    dif, dea, macd_bar, macd_prev = calc_macd(closes)

    c1 = closes[-1] <= mid
    c2 = k < 30
    c3 = j < 20
    c4 = macd_bar > macd_prev and macd_bar < 0
    ok = sum([c1, c2, c3, c4])
    status = "金叉" if dif > dea else "死叉"

    result = {
        "code": code,
        "date": data[-1]["date"],
        "close": closes[-1],
        "boll_pos": round((closes[-1] - lower) / (upper - lower) * 100, 0),
        "mid": round(mid, 1),
        "k": round(k, 1),
        "d": round(d, 1),
        "j": round(j, 1),
        "dif": round(dif, 2),
        "dea": round(dea, 2),
        "macd_bar": round(macd_bar, 2),
        "macd_status": status,
        "c1": c1,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "ok": ok,
        "signal": ok == 4,
    }

    if not quiet:
        name = POOL.get(code, "")
        label = f"{name}({code})" if name else code
        marks = "".join("✅" if x else "❌" for x in [c1, c2, c3, c4])
        print(
            f"{label:<16} {result['date']} 收{closes[-1]:>8.2f}  "
            f"BOLL{result['boll_pos']:>4.0f}%  K{k:>5.1f} J{j:>5.1f}  "
            f"{status} {marks}  {ok}/4{' ← 买入!' if result['signal'] else ''}"
        )

    return result


def main():
    codes = []
    if "--pool" in sys.argv:
        codes = list(POOL.keys())
    else:
        for a in sys.argv[1:]:
            if not a.startswith("-"):
                codes.append(a)

    if not codes:
        print("用法: python screen_buy_signal.py 000001 [000002 ...] [--pool]")
        sys.exit(1)

    print(f"{'标的':<16} {'日期':<12} {'收盘':>8}  BOLL%  {'K':>5} {'J':>5}  MACD  四条件  判定")
    print("-" * 90)
    for code in codes:
        market = 1 if code.startswith("6") else 0
        check(code, market)


if __name__ == "__main__":
    main()
