import urllib.request, json, ssl, math
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ========== 配置区 ==========
STOCKS = [
# 策略参数
BB_PERIOD, BB_STD = 20, 2
KDJ_PERIOD, KDJ_K_SMOOTH, KDJ_D_SMOOTH = 14, 3, 3
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
BUY_K_MAX, BUY_J_MAX = 30, 20

# 样本外分割点：此日期之前 = 样本内（调参），之后 = 样本外（验证）
OOS_SPLIT = "2025-01-01"

# 回测范围
DATE_START = "2023-01-01"
DATE_END = ""
# ============================


def fetch_kline(tx_code, limit=600):
    """拉取前复权日线（腾讯API）"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tx_code},day,,,{limit},qfq"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        text = r.read().decode("gbk", errors="ignore")
    data = json.loads(text)
    klines = data.get("data", {}).get(tx_code, {}).get("qfqday", []) or \
             data.get("data", {}).get(tx_code, {}).get("day", [])
    return klines


def compute_indicators(closes, highs, lows):
    n = len(closes)
    bb_mid, bb_up, bb_down = [], [], []
    for i in range(n):
        if i < BB_PERIOD - 1:
            bb_mid.append(None); bb_up.append(None); bb_down.append(None)
        else:
            w = closes[i - BB_PERIOD + 1:i + 1]
            ma = sum(w) / BB_PERIOD
            std = math.sqrt(sum((x - ma)**2 for x in w) / BB_PERIOD)
            bb_mid.append(ma); bb_up.append(ma + BB_STD * std); bb_down.append(ma - BB_STD * std)

    kdj_k, kdj_d, kdj_j = [50]*n, [50]*n, [50]*n
    for i in range(KDJ_PERIOD, n):
        hh = max(highs[i - KDJ_PERIOD + 1:i + 1])
        ll = min(lows[i - KDJ_PERIOD + 1:i + 1])
        rsv = (closes[i] - ll) / (hh - ll) * 100 if hh != ll else 50
        kdj_k[i] = (KDJ_K_SMOOTH-1)/KDJ_K_SMOOTH * kdj_k[i-1] + 1/KDJ_K_SMOOTH * rsv
        kdj_d[i] = (KDJ_D_SMOOTH-1)/KDJ_D_SMOOTH * kdj_d[i-1] + 1/KDJ_D_SMOOTH * kdj_k[i]
        kdj_j[i] = 3 * kdj_k[i] - 2 * kdj_d[i]

    ema12, ema26 = [None]*n, [None]*n
    dif, dea, macd_bar = [None]*n, [None]*n, [None]*n
    for i in range(n):
        ema12[i] = closes[i] if i == 0 else ema12[i-1]*(1-2/(MACD_FAST+1)) + closes[i]*2/(MACD_FAST+1)
        ema26[i] = closes[i] if i == 0 else ema26[i-1]*(1-2/(MACD_SLOW+1)) + closes[i]*2/(MACD_SLOW+1)
        dif[i] = ema12[i] - ema26[i]
        dea[i] = dif[i] if i == 0 else dea[i-1]*(1-2/(MACD_SIGNAL+1)) + dif[i]*2/(MACD_SIGNAL+1)
        macd_bar[i] = 2 * (dif[i] - dea[i])

    return bb_mid, bb_up, bb_down, kdj_k, kdj_d, kdj_j, dif, dea, macd_bar


def backtest(dates, closes, bb_mid, kdj_k, kdj_j, macd_bar, dif, dea):
    """MACD死叉卖出策略。返回 trades + 每日净值序列。"""
    n = len(closes)
    trades = []
    equity = [1.0] * n
    holding = False
    buy_price = buy_date = ""
    buy_idx = 0

    for i in range(1, n):
        if bb_mid[i] is None:
            equity[i] = equity[i-1]
            continue

        buy_signal = (
            closes[i] <= bb_mid[i]
            and kdj_k[i] < BUY_K_MAX
            and kdj_j[i] < BUY_J_MAX
            and macd_bar[i] > macd_bar[i-1]
        )
        sell_signal = (dif[i] < dea[i] and dif[i-1] >= dea[i-1])

        if (not holding) and buy_signal:
            holding = True
            buy_price = closes[i]; buy_date = dates[i]; buy_idx = i
        elif holding and sell_signal:
            sell_price = closes[i]
            ret = (sell_price - buy_price) / buy_price
            trades.append({
                "buy_date": buy_date, "buy_price": buy_price,
                "sell_date": dates[i], "sell_price": sell_price,
                "return": ret, "days": i - buy_idx
            })
            holding = False

        if holding:
            equity[i] = equity[i-1] * (closes[i] / closes[i-1]) if closes[i-1] != 0 else equity[i-1]
        else:
            equity[i] = equity[i-1]

    if holding:
        ret = (closes[-1] - buy_price) / buy_price
        trades.append({
            "buy_date": buy_date, "buy_price": buy_price,
            "sell_date": dates[-1], "sell_price": closes[-1],
            "return": ret, "days": n - 1 - buy_idx, "note": "持仓中"
        })

    return trades, equity


def calc_metrics(trades, equity, dates):
    """计算：累计收益、胜率、盈亏比、最大回撤、夏普比率"""
    if not trades:
        return {"累计": 0, "笔数": 0, "胜率": "N/A", "盈亏比": "N/A", "最大回撤": "0%", "最大回撤区间": "", "夏普": "N/A"}

    returns = [t["return"] for t in trades]
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]

    cumulative = 1.0
    for r in returns:
        cumulative *= (1 + r)

    # 最大回撤
    peak = equity[0]
    max_dd = 0
    dd_start = dd_end = ""
    in_dd = False
    for i in range(len(equity)):
        if equity[i] > peak:
            peak = equity[i]
            in_dd = False
        dd = (peak - equity[i]) / peak
        if dd > max_dd and dd > 0.001:
            max_dd = dd
            if not in_dd:
                dd_start = dates[i] if i < len(dates) else ""
                in_dd = True
            dd_end = dates[i] if i < len(dates) else ""

    # 盈亏比（平均盈利/平均亏损绝对值）
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0
    profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')

    # 夏普比率（简化版：基于日收益）
    daily_returns = []
    for i in range(1, len(equity)):
        if equity[i-1] > 0:
            daily_returns.append(equity[i] / equity[i-1] - 1)
    if daily_returns:
        avg_dr = sum(daily_returns) / len(daily_returns)
        std_dr = math.sqrt(sum((r - avg_dr)**2 for r in daily_returns) / len(daily_returns))
        sharpe = avg_dr / std_dr * math.sqrt(252) if std_dr > 0 else 0
    else:
        sharpe = 0

    return {
        "累计": f"{(cumulative-1)*100:+.1f}%",
        "笔数": len(trades),
        "胜率": f"{len(wins)}/{len(trades)}={len(wins)/len(trades)*100:.0f}%",
        "盈亏比": f"{profit_factor:.2f}:1" if profit_factor != float('inf') else "∞",
        "最大回撤": f"{max_dd*100:.1f}%",
        "最大回撤区间": f"{dd_start} → {dd_end}" if dd_start else "",
        "夏普": f"{sharpe:.2f}",
        "总盈利": f"{sum(wins)*100:.1f}%" if wins else "0",
        "总亏损": f"{sum(losses)*100:.1f}%" if losses else "0",
    }


def split_periods(dates, closes, highs, lows):
    """按 OOS_SPLIT 分割样本内外"""
    split_idx = 0
    for i, d in enumerate(dates):
        if d >= OOS_SPLIT:
            split_idx = i
            break

    in_dates = dates[:split_idx]; in_closes = closes[:split_idx]
    in_highs = highs[:split_idx]; in_lows = lows[:split_idx]

    out_dates = dates[split_idx:]; out_closes = closes[split_idx:]
    out_highs = highs[split_idx:]; out_lows = lows[split_idx:]

    # 样本外数据需要前 BB_PERIOD 天的样本内数据做指标预热
    warmup = max(BB_PERIOD, KDJ_PERIOD, MACD_SLOW)
    warm_dates = dates[split_idx - warmup:]; warm_closes = closes[split_idx - warmup:]
    warm_highs = highs[split_idx - warmup:]; warm_lows = lows[split_idx - warmup:]

    return (in_dates, in_closes, in_highs, in_lows), \
           (warm_dates, warm_closes, warm_highs, warm_lows), \
           (out_dates, out_closes, out_highs, out_lows)


def print_trades(trades, label):
    """打印交易明细"""
    for t in trades:
        note = f" [{t.get('note','')}]" if t.get('note') else ""
        print(f"  {t['buy_date']} {t['buy_price']:>7.2f} -> {t['sell_date']} {t['sell_price']:>7.2f}  {t['return']*100:>+6.1f}% ({t['days']}天){note}")


def print_metrics(m, label):
    """打印指标"""
    print(f"  {'─'*50}")
    print(f"  {label}")
    print(f"  累计收益: {m['累计']}  |  笔数: {m['笔数']}  |  胜率: {m['胜率']}")
    print(f"  盈亏比:   {m['盈亏比']}  |  最大回撤: {m['最大回撤']}  |  夏普: {m['夏普']}")
    if m['最大回撤区间']:
        print(f"  回撤区间: {m['最大回撤区间']}")


if __name__ == "__main__":
    print("=" * 80)
    print("  富贵竹 — 样本外验证回测")
    print(f"  买入: 收盘≤BB中轨 | K<{BUY_K_MAX} | J<{BUY_J_MAX} | MACD柱收窄")
    print(f"  卖出: MACD死叉(DIF下穿DEA)")
    print(f"  样本内: ~{OOS_SPLIT}  |  样本外: {OOS_SPLIT}~")
    print("=" * 80)

    for code, tx_code, name in STOCKS:
        print(f"\n{'='*80}")
        print(f"  {name} ({code})")
        print(f"{'='*80}")

        klines = fetch_kline(tx_code)
        dates, closes, highs, lows = [], [], [], []
        for k in klines:
            dates.append(k[0]); closes.append(float(k[2]))
            highs.append(float(k[3])); lows.append(float(k[4]))

        # 过滤时间范围
        in_range = []
        for i, d in enumerate(dates):
            if d >= DATE_START and (not DATE_END or d <= DATE_END):
                in_range.append(i)
        if not in_range:
            print("  无数据"); continue
        si, ei = in_range[0], in_range[-1]+1
        dates = dates[si:ei]; closes = closes[si:ei]
        highs = highs[si:ei]; lows = lows[si:ei]

        # 分割样本内外
        (in_dates, in_closes, in_highs, in_lows), \
        (warm_dates, warm_closes, warm_highs, warm_lows), \
        (out_dates, out_closes, out_highs, out_lows) = split_periods(dates, closes, highs, lows)

        # ── 样本内 ──
        bb_mid, bb_up, bb_down, kdj_k, kdj_d, kdj_j, dif, dea, macd_bar = \
            compute_indicators(in_closes, in_highs, in_lows)
        in_trades, in_equity = backtest(in_dates, in_closes, bb_mid, kdj_k, kdj_j, macd_bar, dif, dea)

        # ── 样本外（用预热数据算指标） ──
        bb_mid_o, bb_up_o, bb_down_o, kdj_k_o, kdj_d_o, kdj_j_o, dif_o, dea_o, macd_bar_o = \
            compute_indicators(warm_closes, warm_highs, warm_lows)
        # 切掉预热部分，只保留真正的样本外
        warmup = max(BB_PERIOD, KDJ_PERIOD, MACD_SLOW)
        out_trades, out_equity_full = backtest(
            warm_dates, warm_closes,
            bb_mid_o, kdj_k_o, kdj_j_o, macd_bar_o, dif_o, dea_o
        )
        # 截取样本外期间
        out_equity = out_equity_full[warmup:]
        # 过滤：只有买入日在样本外期间的交易才算
        out_trades_filtered = [t for t in out_trades if t["buy_date"] >= OOS_SPLIT]

        # ── 输出 ──
        if in_trades:
            print(f"\n  📊 样本内 ({in_dates[0]} ~ {in_dates[-1]}) 交易明细:")
            print_trades(in_trades, "")
        m_in = calc_metrics(in_trades, in_equity, in_dates)
        print_metrics(m_in, f"样本内指标 ({in_dates[0]} → {in_dates[-1]})")

        if out_trades_filtered:
            print(f"\n  📊 样本外 ({OOS_SPLIT} ~ {out_dates[-1]}) 交易明细:")
            print_trades(out_trades_filtered, "")
        else:
            print(f"\n  📊 样本外: 无交易信号")
        m_out = calc_metrics(out_trades_filtered, out_equity, out_dates)
        print_metrics(m_out, f"样本外指标 ({OOS_SPLIT} → {out_dates[-1]})")

        # ── 总结 ──
        print(f"\n  {'─'*50}")
        print(f"  🔬 鲁棒性判断:")
        if m_out["笔数"] == 0:
            print(f"     ⚠️ 样本外无信号——策略可能过拟合，或市场环境不匹配")
        else:
            in_cumul = float(m_in["累计"].replace('%','').replace('+',''))
            out_cumul = float(m_out["累计"].replace('%','').replace('+',''))
            ratio = out_cumul / in_cumul if in_cumul != 0 else 0
            pass_robust = out_cumul > 0 and ratio > 0.3
            print(f"     样本内累计: {m_in['累计']}  →  样本外累计: {m_out['累计']}")
            print(f"     样本外/样本内: {ratio*100:.0f}%")
            print(f"     {'✅ 通过：样本外持续盈利，策略有鲁棒性' if pass_robust else '⚠️ 样本外衰减严重，策略可能过拟合'}")
            print(f"     最大回撤: {m_out['最大回撤']} — 实盘前确认你能承受这个幅度")
