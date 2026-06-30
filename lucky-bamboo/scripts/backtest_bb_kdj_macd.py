import urllib.request, json, ssl, math

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ========== 配置区：改这里 ==========
STOCKS = [
]

# 策略参数
BB_PERIOD = 20        # 布林带周期
BB_STD = 2            # 标准差倍数
KDJ_PERIOD = 14       # KDJ周期
KDJ_K_SMOOTH = 3      # K平滑
KDJ_D_SMOOTH = 3      # D平滑
MACD_FAST = 12        # 快线
MACD_SLOW = 26        # 慢线
MACD_SIGNAL = 9       # 信号线

# 买入条件
BUY_K_MAX = 30        # K < 此值
BUY_J_MAX = 20        # J < 此值
BUY_BB_MAX = 50       # 价格 ≤ 中轨（百分比，50=中轨）

# 卖出条件
SELL_MODE = "macd_death"  # "macd_death"=MACD死叉卖出(v2.0推荐) | "touch"=碰轨就卖(v1.0)
SELL_BB_MIN = 0.98        # 价格 ≥ 上轨 × 此值（仅 SELL_MODE="touch" 时使用）

# 回测时间范围（留空=全部）
DATE_START = "2025-10-01"
DATE_END = ""          # 留空=到今天

# ====================================


def fetch_kline(tx_code, limit=350):
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tx_code},day,,,{limit},qfq"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        text = r.read().decode("gbk", errors="ignore")
    data = json.loads(text)
    return data.get("data", {}).get(tx_code, {}).get("qfqday", []) or data.get("data", {}).get(tx_code, {}).get("day", [])


def compute_indicators(closes, highs, lows):
    n = len(closes)
    
    # BB
    bb_mid, bb_up, bb_down = [], [], []
    for i in range(n):
        if i < BB_PERIOD - 1:
            bb_mid.append(None); bb_up.append(None); bb_down.append(None)
        else:
            w = closes[i - BB_PERIOD + 1:i + 1]
            ma = sum(w) / BB_PERIOD
            std = math.sqrt(sum((x - ma)**2 for x in w) / BB_PERIOD)
            bb_mid.append(ma)
            bb_up.append(ma + BB_STD * std)
            bb_down.append(ma - BB_STD * std)
    
    # KDJ
    kdj_k, kdj_d, kdj_j = [50]*n, [50]*n, [50]*n
    for i in range(KDJ_PERIOD, n):
        hh = max(highs[i - KDJ_PERIOD + 1:i + 1])
        ll = min(lows[i - KDJ_PERIOD + 1:i + 1])
        rsv = (closes[i] - ll) / (hh - ll) * 100 if hh != ll else 50
        kdj_k[i] = (KDJ_K_SMOOTH - 1) / KDJ_K_SMOOTH * kdj_k[i-1] + 1/KDJ_K_SMOOTH * rsv
        kdj_d[i] = (KDJ_D_SMOOTH - 1) / KDJ_D_SMOOTH * kdj_d[i-1] + 1/KDJ_D_SMOOTH * kdj_k[i]
        kdj_j[i] = 3 * kdj_k[i] - 2 * kdj_d[i]
    
    # MACD
    ema12, ema26 = [None]*n, [None]*n
    dif, dea, macd_bar = [None]*n, [None]*n, [None]*n
    for i in range(n):
        if i == 0:
            ema12[i] = closes[i]; ema26[i] = closes[i]
        else:
            ema12[i] = ema12[i-1] * (1 - 2/(MACD_FAST+1)) + closes[i] * 2/(MACD_FAST+1)
            ema26[i] = ema26[i-1] * (1 - 2/(MACD_SLOW+1)) + closes[i] * 2/(MACD_SLOW+1)
        dif[i] = ema12[i] - ema26[i]
        dea[i] = dif[i] if i == 0 else dea[i-1] * (1 - 2/(MACD_SIGNAL+1)) + dif[i] * 2/(MACD_SIGNAL+1)
        macd_bar[i] = 2 * (dif[i] - dea[i])
    
    return bb_mid, bb_up, bb_down, kdj_k, kdj_d, kdj_j, dif, dea, macd_bar


def backtest(dates, closes, bb_mid, bb_up, bb_down, kdj_k, kdj_j, macd_bar, dif, dea):
    """sell_mode 由全局 SELL_MODE 控制: 'macd_death' 或 'touch'"""
    n = len(closes)
    trades = []
    holding = False
    buy_price = buy_date = ""
    buy_idx = 0
    
    start_idx = 0
    if DATE_START:
        for i in range(n):
            if dates[i] >= DATE_START: start_idx = i; break
    
    for i in range(start_idx + 1, n):
        if bb_mid[i] is None: continue
        
        buy_signal = (
            closes[i] <= bb_mid[i] * (BUY_BB_MAX / 50)
            and kdj_k[i] < BUY_K_MAX
            and kdj_j[i] < BUY_J_MAX
            and i > 0
            and macd_bar[i] > macd_bar[i-1]
        )
        
        if SELL_MODE == "macd_death":
            sell_signal = (i > 0 and dif[i] < dea[i] and dif[i-1] >= dea[i-1])
        else:
            sell_signal = closes[i] >= bb_up[i] * SELL_BB_MIN
        
        if (not holding) and buy_signal:
            holding = True
            buy_price = closes[i]
            buy_date = dates[i]
            buy_idx = i
        elif holding and sell_signal:
            sell_price = closes[i]
            ret = (sell_price - buy_price) / buy_price * 100
            days = i - buy_idx
            trades.append({
                "buy_date": buy_date, "buy_price": buy_price,
                "sell_date": dates[i], "sell_price": sell_price,
                "return": round(ret, 2), "days": days
            })
            holding = False
    
    if holding:
        ret = (closes[-1] - buy_price) / buy_price * 100
        trades.append({
            "buy_date": buy_date, "buy_price": buy_price,
            "sell_date": dates[-1], "sell_price": closes[-1],
            "return": round(ret, 2), "days": n - 1 - buy_idx, "note": "持仓中"
        })
    
    return trades


if __name__ == "__main__":
    print("=" * 80)
    print("  富贵竹 — 布林带+KDJ+MACD 技术回测")
    print(f"  买入: 收盘≤中轨×{BUY_BB_MAX/50:.1f} | K<{BUY_K_MAX} | J<{BUY_J_MAX} | MACD柱收窄")
    print(f"  卖出: {'MACD死叉(DIF下穿DEA)' if SELL_MODE=='macd_death' else f'收盘≥上轨×{SELL_BB_MIN}'}")
    print("=" * 80)
    
    for code, tx_code, name in STOCKS:
        klines = fetch_kline(tx_code)
        dates, closes, highs, lows = [], [], [], []
        for k in klines:
            p = k
            dates.append(p[0]); closes.append(float(p[2]))
            highs.append(float(p[3])); lows.append(float(p[4]))
        
        bb_mid, bb_up, bb_down, kdj_k, kdj_d, kdj_j, dif, dea, macd_bar = compute_indicators(closes, highs, lows)
        trades = backtest(dates, closes, bb_mid, bb_up, bb_down, kdj_k, kdj_j, macd_bar, dif, dea)
        
        print(f"\n  {name} ({code})")
        if len(trades) == 0:
            print(f"  无交易信号")
        else:
            returns = [t["return"] for t in trades]
            wins = sum(1 for r in returns if r > 0)
            for t in trades:
                note = f" [{t.get('note','')}]" if t.get('note') else ""
                print(f"  {t['buy_date']} {t['buy_price']:>8.2f} -> {t['sell_date']} {t['sell_price']:>8.2f}  {t['return']:>+7.2f}% ({t['days']}天){note}")
            print(f"  {len(trades)}笔 | 胜率{wins}/{len(trades)}={wins/len(trades)*100:.0f}% | 累计{sum(returns):+.1f}% | 平均{sum(returns)/len(returns):+.1f}%")
